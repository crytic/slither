import logging
from math import floor
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import dataclasses

from eth_abi import decode, encode
from eth_typing.evm import ChecksumAddress
from eth_utils import keccak, to_checksum_address
from web3 import Web3
from web3.types import BlockIdentifier
from web3.exceptions import ExtraDataLengthError
from web3.middleware import geth_poa_middleware

from slither.core.declarations import Contract, Structure
from slither.core.solidity_types import ArrayType, ElementaryType, MappingType, UserDefinedType
from slither.core.solidity_types.type import Type
from slither.core.cfg.node import NodeType
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.structure_variable import StructureVariable
from slither.core.expressions import (
    AssignmentOperation,
    Literal,
    Identifier,
    BinaryOperation,
    UnaryOperation,
    TupleExpression,
    TypeConversion,
    CallExpression,
)
from slither.utils.myprettytable import MyPrettyTable
from slither.visitors.expression.constants_folding import ConstantFolding, NotConstant

from .utils import coerce_type, get_offset_value, get_storage_data

logging.basicConfig()
logger = logging.getLogger("Slither-read-storage")
logger.setLevel(logging.INFO)

Elem = Dict[str, "SlotInfo"]
NestedElem = Dict[str, Elem]


@dataclasses.dataclass
class SlotInfo:
    name: str
    type_string: str
    slot: int
    size: int
    offset: int
    value: Optional[Union[int, bool, str, ChecksumAddress]] = None
    # For structure and array, str->SlotInfo
    elems: Union[Elem, NestedElem] = dataclasses.field(default_factory=lambda: {})  # type: ignore[assignment]


class SlitherReadStorageException(Exception):
    pass


class RpcInfo:
    def __init__(self, rpc_url: str, block: BlockIdentifier = "latest") -> None:
        assert isinstance(block, int) or block in [
            "latest",
            "earliest",
            "pending",
            "safe",
            "finalized",
        ]
        self.rpc: str = rpc_url
        self._web3: Web3 = Web3(Web3.HTTPProvider(self.rpc))
        """If the RPC is for a POA network, the first call to get_block fails, so we inject geth_poa_middleware"""
        try:
            self._block: int = self.web3.eth.get_block(block)["number"]
        except ExtraDataLengthError:
            self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            self._block: int = self.web3.eth.get_block(block)["number"]

    @property
    def web3(self) -> Web3:
        return self._web3

    @property
    def block(self) -> int:
        return self._block


# pylint: disable=too-many-instance-attributes,too-many-public-methods
class SlitherReadStorage:
    def __init__(self, contracts: List[Contract], max_depth: int, rpc_info: RpcInfo = None) -> None:
        self._checksum_address: Optional[ChecksumAddress] = None
        self._contracts: List[Contract] = contracts
        self._log: str = ""
        self._max_depth: int = max_depth
        self._slot_info: Dict[str, SlotInfo] = {}
        self._target_variables: List[Tuple[Contract, StateVariable]] = []
        self._constant_storage_slots: List[Tuple[Contract, StateVariable]] = []
        self.rpc_info: Optional[RpcInfo] = rpc_info
        self.storage_address: Optional[str] = None
        self.table: Optional[MyPrettyTable] = None
        self.unstructured: bool = False

    @property
    def contracts(self) -> List[Contract]:
        return self._contracts

    @property
    def max_depth(self) -> int:
        return int(self._max_depth)

    @property
    def log(self) -> str:
        return self._log

    @log.setter
    def log(self, log: str) -> None:
        self._log = log

    @property
    def checksum_address(self) -> ChecksumAddress:
        if not self.storage_address:
            raise ValueError
        if not self._checksum_address:
            self._checksum_address = to_checksum_address(self.storage_address)
        return self._checksum_address

    @property
    def target_variables(self) -> List[Tuple[Contract, StateVariable]]:
        """Storage variables (not constant or immutable) and their associated contract."""
        return self._target_variables

    @property
    def constant_slots(self) -> List[Tuple[Contract, StateVariable]]:
        """Constant bytes32 variables and their associated contract."""
        return self._constant_storage_slots

    @property
    def slot_info(self) -> Dict[str, SlotInfo]:
        """Contains the location, type, size, offset, and value of contract slots."""
        return self._slot_info

    def get_storage_layout(self) -> None:
        """Retrieves the storage layout of entire contract."""
        tmp: Dict[str, SlotInfo] = {}
        for contract, var in self.target_variables:
            type_ = var.type
            info = self.get_storage_slot(var, contract)
            if info:
                tmp[var.name] = info
                if isinstance(type_, UserDefinedType) and isinstance(type_.type, Structure):
                    tmp[var.name].elems = self._all_struct_slots(var, type_.type, contract)

                elif isinstance(type_, ArrayType):
                    elems = self._all_array_slots(var, contract, type_, info.slot)
                    tmp[var.name].elems = elems
        if self.unstructured:
            tmp.update(self.get_unstructured_layout())
        self._slot_info = tmp

    def get_unstructured_layout(self) -> Dict[str, SlotInfo]:
        tmp: Dict[str, SlotInfo] = {}
        for _, var in self.constant_slots:
            var_name = var.name
            try:
                exp = var.expression
                if isinstance(
                    exp,
                    (
                        BinaryOperation,
                        UnaryOperation,
                        Identifier,
                        TupleExpression,
                        TypeConversion,
                        CallExpression,
                    ),
                ):
                    exp = ConstantFolding(exp, "bytes32").result()
                if isinstance(exp, Literal):
                    slot = coerce_type("int", exp.value)
                else:
                    continue
                offset = 0
                type_string, size = self.find_constant_slot_storage_type(var)
                if type_string:
                    tmp[var.name] = SlotInfo(
                        name=var_name, type_string=type_string, slot=slot, size=size, offset=offset
                    )
                    self.log += (
                        f"\nSlot Name: {var_name}\nType: bytes32"
                        f"\nStorage Type: {type_string}\nSlot: {str(exp)}\n"
                    )
                    logger.info(self.log)
                    self.log = ""
            except NotConstant:
                continue
        return tmp

    # TODO: remove this pylint exception (montyly)
    # pylint: disable=too-many-locals
    def get_storage_slot(
        self,
        target_variable: StateVariable,
        contract: Contract,
        **kwargs: Any,
    ) -> Union[SlotInfo, None]:
        """
        Finds the storage slot of a variable in a given contract.
        Args:
            target_variable (`StateVariable`): The variable to retrieve the slot for.
            contracts (`Contract`): The contract that contains the given state variable.
        **kwargs:
            key (int): Key of a mapping or index position if an array.
            deep_key (int): Key of a mapping embedded within another mapping or
            secondary index if array.
            struct_var (str): Structure variable name.
        Returns:
            (`SlotInfo`) | None : A dictionary of the slot information.
        """

        key: Optional[int] = kwargs.get("key", None)
        deep_key: Optional[int] = kwargs.get("deep_key", None)
        struct_var: Optional[str] = kwargs.get("struct_var", None)
        info: str
        var_log_name = target_variable.name
        try:
            int_slot, size, offset, type_to = self.get_variable_info(contract, target_variable)
        except KeyError:
            # Only the child contract of a parent contract will show up in the storage layout when inheritance is used
            logger.info(
                f"\nContract {contract} not found in storage layout. It is possibly a parent contract\n"
            )
            return None

        slot = int.to_bytes(int_slot, 32, byteorder="big")

        target_variable_type = target_variable.type

        if isinstance(target_variable_type, ElementaryType):
            type_to = target_variable_type.name

        elif isinstance(target_variable_type, ArrayType) and key is not None:
            var_log_name = f"{var_log_name}[{key}]"
            info, type_to, slot, size, offset = self._find_array_slot(
                target_variable_type,
                slot,
                key,
                deep_key=deep_key,
                struct_var=struct_var,
            )
            self.log += info

        elif isinstance(target_variable_type, UserDefinedType) and struct_var is not None:
            var_log_name = f"{var_log_name}.{struct_var}"
            target_variable_type_type = target_variable_type.type
            assert isinstance(target_variable_type_type, Structure)
            elems = target_variable_type_type.elems_ordered
            info, type_to, slot, size, offset = self._find_struct_var_slot(elems, slot, struct_var)
            self.log += info

        elif isinstance(target_variable_type, MappingType) and key:
            info, type_to, slot, size, offset = self._find_mapping_slot(
                target_variable_type, slot, key, struct_var=struct_var, deep_key=deep_key
            )
            self.log += info

        int_slot = int.from_bytes(slot, byteorder="big")
        self.log += f"\nName: {var_log_name}\nType: {type_to}\nSlot: {int_slot}\n"
        logger.info(self.log)
        self.log = ""

        return SlotInfo(
            name=var_log_name,
            type_string=type_to,
            slot=int_slot,
            size=size,
            offset=offset,
        )

    def get_target_variables(self, **kwargs) -> None:
        """
        Retrieves every instance of a given variable in a list of contracts.
        Should be called after setting `target_variables` with `get_all_storage_variables()`.
        **kwargs:
            key (str): Key of a mapping or index position if an array.
            deep_key (str): Key of a mapping embedded within another mapping or secondary index if array.
            struct_var (str): Structure variable name.
        """
        for contract, var in self.target_variables:
            slot_info = self.get_storage_slot(var, contract, **kwargs)
            if slot_info:
                self._slot_info[f"{contract.name}.{var.name}"] = slot_info

    def find_constant_slot_storage_type(
        self, var: StateVariable
    ) -> Tuple[Optional[str], Optional[int]]:
        """
        Given a constant bytes32 StateVariable, tries to determine which variable type is stored there, using the
        heuristic that if a function reads from the slot and returns a value, it probably stores that type of value.
        Also uses the StorageSlot library as a heuristic when a function has no return but uses the library's getters.
        Args:
            var (StateVariable): The constant bytes32 storage slot.

        Returns:
            type (str): The type of value stored in the slot.
            size (int): The type's size in bits.
        """
        assert var.is_constant and var.type == ElementaryType("bytes32")
        storage_type = None
        size = None
        funcs = []
        for c in self.contracts:
            c_funcs = c.get_functions_reading_from_variable(var)
            c_funcs.extend(
                f
                for f in c.functions
                if any(str(v.expression) == str(var.expression) for v in f.variables)
            )
            c_funcs = list(set(c_funcs))
            funcs.extend(c_funcs)
        fallback = [f for f in var.contract.functions if f.is_fallback]
        funcs += fallback
        for func in funcs:
            rets = func.return_type if func.return_type is not None else []
            for ret in rets:
                size, _ = ret.storage_size
                if size <= 32:
                    return str(ret), size * 8
            for node in func.all_nodes():
                exp = node.expression
                # Look for use of the common OpenZeppelin StorageSlot library
                if f"getAddressSlot({var.name})" in str(exp):
                    return "address", 160
                if f"getBooleanSlot({var.name})" in str(exp):
                    return "bool", 1
                if f"getBytes32Slot({var.name})" in str(exp):
                    return "bytes32", 256
                if f"getUint256Slot({var.name})" in str(exp):
                    return "uint256", 256
                # Look for variable assignment in assembly loaded from a hardcoded slot
                if (
                    isinstance(exp, AssignmentOperation)
                    and isinstance(exp.expression_left, Identifier)
                    and isinstance(exp.expression_right, CallExpression)
                    and "sload" in str(exp.expression_right.called)
                    and str(exp.expression_right.arguments[0]) == str(var.expression)
                ):
                    if func.is_fallback:
                        return "address", 160
                    storage_type = exp.expression_left.value.type.name
                    size, _ = exp.expression_left.value.type.storage_size
                    return storage_type, size * 8
                # Look for variable storage in assembly stored to a hardcoded slot
                if (
                    isinstance(exp, CallExpression)
                    and "sstore" in str(exp.called)
                    and isinstance(exp.arguments[0], Identifier)
                    and isinstance(exp.arguments[1], Identifier)
                    and str(exp.arguments[0].value.expression) == str(var.expression)
                ):
                    storage_type = exp.arguments[1].value.type.name
                    size, _ = exp.arguments[1].value.type.storage_size
                    return storage_type, size * 8
        return storage_type, size

    def walk_slot_info(self, func: Callable) -> None:
        stack = list(self.slot_info.values())
        while stack:
            slot_info = stack.pop()
            if isinstance(slot_info, dict):  # NestedElem
                stack.extend(slot_info.values())
            elif slot_info.elems:
                stack.extend(list(slot_info.elems.values()))
            if isinstance(slot_info, SlotInfo):
                func(slot_info)

    def get_slot_values(self, slot_info: SlotInfo) -> None:
        """
        Fetches the slot value of `SlotInfo` object
        :param slot_info:
        """
        assert self.rpc_info is not None
        hex_bytes = get_storage_data(
            self.rpc_info.web3,
            self.checksum_address,
            int.to_bytes(slot_info.slot, 32, byteorder="big"),
            self.rpc_info.block,
        )
        slot_info.value = self.convert_value_to_type(
            hex_bytes, slot_info.size, slot_info.offset, slot_info.type_string
        )
        logger.info(f"\nValue: {slot_info.value}\n")

    def get_all_storage_variables(self, func: Callable = lambda x: x) -> None:
        """
        Fetches all storage variables from a list of contracts.
        kwargs:
            func (Callable, optional): A criteria to filter functions e.g. name.
        """
        for contract in self.contracts:
            for var in contract.state_variables_ordered:
                if func(var):
                    if not var.is_constant and not var.is_immutable:
                        self._target_variables.append((contract, var))
                    elif (
                        self.unstructured
                        and var.is_constant
                        and var.type == ElementaryType("bytes32")
                    ):
                        self._constant_storage_slots.append((contract, var))
            if self.unstructured:
                hardcoded_slot = self.find_hardcoded_slot_in_fallback(contract)
                if hardcoded_slot is not None:
                    self._constant_storage_slots.append((contract, hardcoded_slot))

    def find_hardcoded_slot_in_fallback(self, contract: Contract) -> Optional[StateVariable]:
        """
        Searches the contract's fallback function for a sload from a literal storage slot, i.e.,
        `let contractLogic := sload(0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7)`.

        Args:
            contract: a Contract object, which should have a fallback function.

        Returns:
            A newly created StateVariable representing the Literal bytes32 slot, if one is found, otherwise None.
        """
        fallback = None
        for func in contract.functions_entry_points:
            if func.is_fallback:
                fallback = func
                break
        if fallback is None:
            return None
        queue = [fallback.entry_point]
        visited = []
        while len(queue) > 0:
            node = queue.pop(0)
            visited.append(node)
            queue.extend(son for son in node.sons if son not in visited)
            if node.type == NodeType.ASSEMBLY and isinstance(node.inline_asm, str):
                return SlitherReadStorage.find_hardcoded_slot_in_asm_str(node.inline_asm, contract)
            if node.type == NodeType.EXPRESSION:
                sv = self.find_hardcoded_slot_in_exp(node.expression, contract)
                if sv is not None:
                    return sv
        return None

    @staticmethod
    def find_hardcoded_slot_in_asm_str(
        inline_asm: str, contract: Contract
    ) -> Optional[StateVariable]:
        """
        Searches a block of assembly code (given as a string) for a sload from a literal storage slot.
        Does not work if the argument passed to sload does not start with "0x", i.e., `sload(add(1,1))`
        or `and(sload(0), 0xffffffffffffffffffffffffffffffffffffffff)`.

        Args:
            inline_asm: a string containing all the code in an assembly node (node.inline_asm for solc < 0.6.0).

        Returns:
            A newly created StateVariable representing the Literal bytes32 slot, if one is found, otherwise None.
        """
        asm_split = inline_asm.split("\n")
        for asm in asm_split:
            if "sload(" in asm:  # Only handle literals
                arg = asm.split("sload(")[1].split(")")[0]
                if arg.startswith("0x"):
                    exp = Literal(arg, ElementaryType("bytes32"))
                    sv = StateVariable()
                    sv.name = "fallback_sload_hardcoded"
                    sv.expression = exp
                    sv.is_constant = True
                    sv.type = exp.type
                    sv.set_contract(contract)
                    return sv
        return None

    def find_hardcoded_slot_in_exp(
        self, exp: "Expression", contract: Contract
    ) -> Optional[StateVariable]:
        """
        Parses an expression to see if it contains a sload from a literal storage slot,
        unrolling nested expressions if necessary to determine which slot it loads from.
        Args:
            exp: an Expression object to search.
            contract: the Contract containing exp.

        Returns:
            A newly created StateVariable representing the Literal bytes32 slot, if one is found, otherwise None.
        """
        if isinstance(exp, AssignmentOperation):
            exp = exp.expression_right
        while isinstance(exp, BinaryOperation):
            exp = next(
                (e for e in exp.expressions if isinstance(e, (CallExpression, BinaryOperation))),
                exp.expression_left,
            )
        while isinstance(exp, CallExpression) and len(exp.arguments) > 0:
            called = exp.called
            exp = exp.arguments[0]
            if "sload" in str(called):
                break
        if isinstance(
            exp,
            (
                BinaryOperation,
                UnaryOperation,
                Identifier,
                TupleExpression,
                TypeConversion,
                CallExpression,
            ),
        ):
            try:
                exp = ConstantFolding(exp, "bytes32").result()
            except NotConstant:
                return None
        if (
            isinstance(exp, Literal)
            and isinstance(exp.type, ElementaryType)
            and exp.type.name in ["bytes32", "uint256"]
        ):
            sv = StateVariable()
            sv.name = "fallback_sload_hardcoded"
            value = exp.value
            str_value = str(value)
            if str_value.isdecimal():
                value = int(value)
            if isinstance(value, (int, bytes)):
                if isinstance(value, bytes):
                    str_value = "0x" + value.hex()
                    value = int(str_value, 16)
                exp = Literal(str_value, ElementaryType("bytes32"))
                state_var_slots = [
                    self.get_variable_info(contract, var)[0]
                    for contract, var in self.target_variables
                ]
                if value in state_var_slots:
                    return None
            sv.expression = exp
            sv.is_constant = True
            sv.type = ElementaryType("bytes32")
            sv.set_contract(contract)
            return sv
        return None

    def convert_slot_info_to_rows(self, slot_info: SlotInfo) -> None:
        """
        Convert and append slot info to table. Create table if it
        does not yet exist
        :param slot_info:
        """
        field_names = [
            field.name for field in dataclasses.fields(SlotInfo) if field.name != "elems"
        ]
        if not self.table:
            self.table = MyPrettyTable(field_names)
        self.table.add_row([getattr(slot_info, field) for field in field_names])

    def to_json(self) -> Dict:
        return {key: dataclasses.asdict(value) for key, value in self.slot_info.items()}

    @staticmethod
    def _find_struct_var_slot(
        elems: List[StructureVariable], slot_as_bytes: bytes, struct_var: str
    ) -> Tuple[str, str, bytes, int, int]:
        """
        Finds the slot of a structure variable.
        Args:
            elems (List[StructureVariable]): Ordered list of structure variables.
            slot_as_bytes (bytes): The slot of the struct to begin searching at.
            struct_var (str): The target structure variable.
        Returns:
            info (str): Info about the target variable to log.
            type_to (str): The type of the target variable.
            slot (bytes): The storage location of the target variable.
            size (int): The size (in bits) of the target variable.
            offset (int): The size of other variables that share the same slot.
        """
        slot = int.from_bytes(slot_as_bytes, "big")
        offset = 0
        type_to = ""
        for var in elems:
            var_type = var.type
            if isinstance(var_type, ElementaryType):
                size = var_type.size
                if offset >= 256:
                    slot += 1
                    offset = 0
                if struct_var == var.name:
                    type_to = var_type.name
                    break  # found struct var
                offset += size
            else:
                logger.info(f"{type(var_type)} is current not implemented in _find_struct_var_slot")

        slot_as_bytes = int.to_bytes(slot, 32, byteorder="big")
        info = f"\nStruct Variable: {struct_var}"
        return info, type_to, slot_as_bytes, size, offset

    # pylint: disable=too-many-branches,too-many-statements
    @staticmethod
    def _find_array_slot(
        target_variable_type: ArrayType,
        slot: bytes,
        key: int,
        deep_key: int = None,
        struct_var: str = None,
    ) -> Tuple[str, str, bytes, int, int]:
        """
        Finds the slot of array's index.
        Args:
            target_variable (`StateVariable`): The array that contains the target variable.
            slot (bytes): The starting slot of the array.
            key (int): The target variable's index position.
            deep_key (int, optional): Secondary index if nested array.
            struct_var (str, optional): Structure variable name.
        Returns:
            info (str): Info about the target variable to log.
            type_to (str): The type of the target variable.
            slot (bytes): The storage location of the target variable.
            size (int): The size
            offset (int): The offset
        """
        info = f"\nKey: {key}"
        offset = 0
        size = 256

        target_variable_type_type = target_variable_type.type

        if isinstance(
            target_variable_type_type, ArrayType
        ):  # multidimensional array uint[i][], , uint[][i], or uint[][]
            assert isinstance(target_variable_type_type.type, ElementaryType)
            size = target_variable_type_type.type.size
            type_to = target_variable_type_type.type.name

            if target_variable_type.is_fixed_array:  # uint[][i]
                slot_int = int.from_bytes(slot, "big") + int(key)
            else:
                slot = keccak(slot)
                key = int(key)
                if target_variable_type_type.is_fixed_array:  # arr[i][]
                    key *= int(str(target_variable_type_type.length))
                slot_int = int.from_bytes(slot, "big") + key

            if not deep_key:
                return info, type_to, int.to_bytes(slot_int, 32, "big"), size, offset

            info += f"\nDeep Key: {deep_key}"
            if target_variable_type_type.is_dynamic_array:  # uint[][]
                # keccak256(keccak256(slot) + index) + floor(j / floor(256 / size))
                slot = keccak(int.to_bytes(slot_int, 32, "big"))
                slot_int = int.from_bytes(slot, "big")

            # keccak256(slot) + index + floor(j / floor(256 / size))
            slot_int += floor(int(deep_key) / floor(256 / size))  # uint[i][]

        elif target_variable_type.is_fixed_array:
            slot_int = int.from_bytes(slot, "big") + int(key)
            if isinstance(target_variable_type_type, UserDefinedType) and isinstance(
                target_variable_type_type.type, Structure
            ):  # struct[i]
                type_to = target_variable_type_type.type.name
                if not struct_var:
                    return info, type_to, int.to_bytes(slot_int, 32, "big"), size, offset
                elems = target_variable_type_type.type.elems_ordered
                slot = int.to_bytes(slot_int, 32, byteorder="big")
                info_tmp, type_to, slot, size, offset = SlitherReadStorage._find_struct_var_slot(
                    elems, slot, struct_var
                )
                info += info_tmp

            else:
                assert isinstance(target_variable_type_type, ElementaryType)
                type_to = target_variable_type_type.name
                size = target_variable_type_type.size  # bits

        elif isinstance(target_variable_type_type, UserDefinedType) and isinstance(
            target_variable_type_type.type, Structure
        ):  # struct[]
            slot = keccak(slot)
            slot_int = int.from_bytes(slot, "big") + int(key)
            type_to = target_variable_type_type.type.name
            if not struct_var:
                return info, type_to, int.to_bytes(slot_int, 32, "big"), size, offset
            elems = target_variable_type_type.type.elems_ordered
            slot = int.to_bytes(slot_int, 32, byteorder="big")
            info_tmp, type_to, slot, size, offset = SlitherReadStorage._find_struct_var_slot(
                elems, slot, struct_var
            )
            info += info_tmp

        else:
            assert isinstance(target_variable_type_type, ElementaryType)

            slot = keccak(slot)
            slot_int = int.from_bytes(slot, "big") + int(key)
            type_to = target_variable_type_type.name
            size = target_variable_type_type.size  # bits

        slot = int.to_bytes(slot_int, 32, byteorder="big")

        return info, type_to, slot, size, offset

    @staticmethod
    def _find_mapping_slot(
        target_variable_type: MappingType,
        slot: bytes,
        key: Union[int, str],
        deep_key: Union[int, str] = None,
        struct_var: str = None,
    ) -> Tuple[str, str, bytes, int, int]:
        """
        Finds the data slot of a target variable within a mapping.
            target_variable (`StateVariable`): The mapping that contains the target variable.
            slot (bytes): The starting slot of the mapping.
            key (Union[int, str]): The key the variable is stored at.
            deep_key (int, optional): Key of a mapping embedded within another mapping.
            struct_var (str, optional): Structure variable name.
        :returns:
            log (str): Info about the target variable to log.
            type_to (str): The type of the target variable.
            slot (bytes): The storage location of the target variable.
            size (int): The size (in bits) of the target variable.
            offset (int): The size of other variables that share the same slot.

        """
        info = ""
        offset = 0
        if key:
            info += f"\nKey: {key}"
        if deep_key:
            info += f"\nDeep Key: {deep_key}"
        assert isinstance(target_variable_type.type_from, ElementaryType)
        key_type = target_variable_type.type_from.name
        assert key
        if "int" in key_type:  # without this eth_utils encoding fails
            key = int(key)
        key = coerce_type(key_type, key)
        slot = keccak(encode([key_type, "uint256"], [key, decode(["uint256"], slot)[0]]))

        if isinstance(target_variable_type.type_to, UserDefinedType) and isinstance(
            target_variable_type.type_to.type, Structure
        ):  # mapping(elem => struct)
            assert struct_var
            elems = target_variable_type.type_to.type.elems_ordered
            info_tmp, type_to, slot, size, offset = SlitherReadStorage._find_struct_var_slot(
                elems, slot, struct_var
            )
            info += info_tmp

        elif isinstance(
            target_variable_type.type_to, MappingType
        ):  # mapping(elem => mapping(elem => ???))
            assert deep_key
            assert isinstance(target_variable_type.type_to.type_from, ElementaryType)
            key_type = target_variable_type.type_to.type_from.name
            if "int" in key_type:  # without this eth_utils encoding fails
                deep_key = int(deep_key)

            # If deep map, will be keccak256(abi.encode(key1, keccak256(abi.encode(key0, uint(slot)))))
            slot = keccak(encode([key_type, "bytes32"], [deep_key, slot]))

            # mapping(elem => mapping(elem => elem))
            target_variable_type_type_to_type_to = target_variable_type.type_to.type_to
            assert isinstance(
                target_variable_type_type_to_type_to, (UserDefinedType, ElementaryType)
            )
            type_to = str(target_variable_type_type_to_type_to.type)
            byte_size, _ = target_variable_type_type_to_type_to.storage_size
            size = byte_size * 8  # bits
            offset = 0

            if isinstance(target_variable_type_type_to_type_to, UserDefinedType) and isinstance(
                target_variable_type_type_to_type_to.type, Structure
            ):  # mapping(elem => mapping(elem => struct))
                assert struct_var
                elems = target_variable_type_type_to_type_to.type.elems_ordered
                # If map struct, will be bytes32(uint256(keccak256(abi.encode(key1, keccak256(abi.encode(key0, uint(slot)))))) + structFieldDepth);
                info_tmp, type_to, slot, size, offset = SlitherReadStorage._find_struct_var_slot(
                    elems, slot, struct_var
                )
                info += info_tmp

        # TODO: support mapping with dynamic arrays

        # mapping(elem => elem)
        elif isinstance(target_variable_type.type_to, ElementaryType):
            type_to = target_variable_type.type_to.name  # the value's elementary type
            byte_size, _ = target_variable_type.type_to.storage_size
            size = byte_size * 8  # bits

        else:
            raise NotImplementedError(
                f"{target_variable_type} => {target_variable_type.type_to} not implemented"
            )

        return info, type_to, slot, size, offset

    @staticmethod
    def get_variable_info(
        contract: Contract, target_variable: StateVariable
    ) -> Tuple[int, int, int, str]:
        """Return slot, size, offset, and type."""
        assert isinstance(target_variable.type, Type)
        type_to = str(target_variable.type)
        byte_size, _ = target_variable.type.storage_size
        size = byte_size * 8  # bits
        (int_slot, offset) = contract.compilation_unit.storage_layout_of(contract, target_variable)
        offset *= 8  # bits
        logger.info(
            f"\nContract '{contract.name}'\n{target_variable.canonical_name} with type {target_variable.type} is located at slot: {int_slot}\n"
        )

        return int_slot, size, offset, type_to

    @staticmethod
    def convert_value_to_type(
        hex_bytes: bytes, size: int, offset: int, type_to: str
    ) -> Union[int, bool, str, ChecksumAddress]:
        """Convert slot data to type representation."""
        # Account for storage packing
        offset_hex_bytes = get_offset_value(hex_bytes, offset, size)
        try:
            value = coerce_type(type_to, offset_hex_bytes)
        except ValueError:
            return coerce_type("int", offset_hex_bytes)

        return value

    def _all_struct_slots(
        self, var: StateVariable, st: Structure, contract: Contract, key: Optional[int] = None
    ) -> Elem:
        """Retrieves all members of a struct."""
        struct_elems = st.elems_ordered
        data: Elem = {}
        for elem in struct_elems:
            info = self.get_storage_slot(
                var,
                contract,
                key=key,
                struct_var=elem.name,
            )
            if info:
                data[elem.name] = info

        return data

    # pylint: disable=too-many-nested-blocks
    def _all_array_slots(
        self, var: StateVariable, contract: Contract, type_: ArrayType, slot: int
    ) -> Union[Elem, NestedElem]:
        """Retrieves all members of an array."""
        array_length = self._get_array_length(type_, slot)
        target_variable_type = type_.type
        if isinstance(target_variable_type, UserDefinedType) and isinstance(
            target_variable_type.type, Structure
        ):
            nested_elems: NestedElem = {}
            for i in range(min(array_length, self.max_depth)):
                nested_elems[str(i)] = self._all_struct_slots(
                    var, target_variable_type.type, contract, key=i
                )
            return nested_elems

        elems: Elem = {}
        for i in range(min(array_length, self.max_depth)):
            info = self.get_storage_slot(
                var,
                contract,
                key=str(i),
            )
            if info:
                elems[str(i)] = info

                if isinstance(target_variable_type, ArrayType):  # multidimensional array
                    array_length = self._get_array_length(target_variable_type, info.slot)

                    for j in range(min(array_length, self.max_depth)):
                        info = self.get_storage_slot(
                            var,
                            contract,
                            key=str(i),
                            deep_key=str(j),
                        )
                        if info:
                            elems[str(i)].elems[str(j)] = info
        return elems

    def _get_array_length(self, type_: Type, slot: int) -> int:
        """
        Gets the length of dynamic and fixed arrays.
        Args:
            type_ (`AbstractType`): The array type.
            slot (int): Slot a dynamic array's length is stored at.
        Returns:
            (int): The length of the array.
        """
        val = 0
        if self.rpc_info:
            # The length of dynamic arrays is stored at the starting slot.
            # Convert from hexadecimal to decimal.
            val = int(
                get_storage_data(
                    self.rpc_info.web3,
                    self.checksum_address,
                    int.to_bytes(slot, 32, byteorder="big"),
                    self.rpc_info.block,
                ).hex(),
                16,
            )
        if isinstance(type_, ArrayType):
            if type_.is_fixed_array:
                val = int(str(type_.length))

        return val
