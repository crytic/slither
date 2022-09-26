import logging
import sys
from math import floor
from typing import Callable, Optional, Tuple, Union, List, Dict, Any

try:
    from web3 import Web3
    from eth_typing.evm import ChecksumAddress
    from eth_abi import decode_single, encode_abi
    from eth_utils import keccak
    from .utils import (
        get_offset_value,
        get_storage_data,
        coerce_type,
    )
except ImportError:
    print("ERROR: in order to use slither-read-storage, you need to install web3")
    print("$ pip3 install web3 --user\n")
    sys.exit(-1)

import dataclasses
from slither.utils.myprettytable import MyPrettyTable
from slither.core.solidity_types.type import Type
from slither.core.solidity_types import ArrayType, ElementaryType, UserDefinedType, MappingType
from slither.core.declarations import Contract, Structure
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.structure_variable import StructureVariable

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


# pylint: disable=too-many-instance-attributes
class SlitherReadStorage:
    def __init__(self, contracts: List[Contract], max_depth: int) -> None:
        self._contracts: List[Contract] = contracts
        self._max_depth: int = max_depth
        self._log: str = ""
        self._slot_info: Dict[str, SlotInfo] = {}
        self._target_variables: List[Tuple[Contract, StateVariable]] = []
        self._web3: Optional[Web3] = None
        self._checksum_address: Optional[ChecksumAddress] = None
        self.storage_address: Optional[str] = None
        self.rpc: Optional[str] = None
        self.table: Optional[MyPrettyTable] = None

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
    def web3(self) -> Web3:
        if not self._web3:
            self._web3 = Web3(Web3.HTTPProvider(self.rpc))
        return self._web3

    @property
    def checksum_address(self) -> ChecksumAddress:
        if not self.storage_address:
            raise ValueError
        if not self._checksum_address:
            self._checksum_address = self.web3.toChecksumAddress(self.storage_address)
        return self._checksum_address

    @property
    def target_variables(self) -> List[Tuple[Contract, StateVariable]]:
        """Storage variables (not constant or immutable) and their associated contract."""
        return self._target_variables

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

        self._slot_info = tmp

    # TODO: remove this pylint exception (montyly)
    # pylint: disable=too-many-locals
    def get_storage_slot(
        self,
        target_variable: StateVariable,
        contract: Contract,
        **kwargs: Any,
    ) -> Union[SlotInfo, None]:
        """Finds the storage slot of a variable in a given contract.
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
        """Fetches the slot value of `SlotInfo` object
        :param slot_info:
        """
        hex_bytes = get_storage_data(
            self.web3, self.checksum_address, int.to_bytes(slot_info.slot, 32, byteorder="big"), self.block
        )
        slot_info.value = self.convert_value_to_type(
            hex_bytes, slot_info.size, slot_info.offset, slot_info.type_string
        )
        logger.info(f"\nValue: {slot_info.value}\n")

    def get_all_storage_variables(self, func: Callable = None) -> None:
        """Fetches all storage variables from a list of contracts.
        kwargs:
            func (Callable, optional): A criteria to filter functions e.g. name.
        """
        for contract in self.contracts:
            self._target_variables.extend(
                filter(
                    func,
                    [
                        (contract, var)
                        for var in contract.variables
                        if not var.is_constant and not var.is_immutable
                    ],
                )
            )

    def convert_slot_info_to_rows(self, slot_info: SlotInfo) -> None:
        """Convert and append slot info to table. Create table if it
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
        """Finds the slot of a structure variable.
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
        """Finds the slot of array's index.
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
        """Finds the data slot of a target variable within a mapping.
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
        slot = keccak(encode_abi([key_type, "uint256"], [key, decode_single("uint256", slot)]))

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
            slot = keccak(encode_abi([key_type, "bytes32"], [deep_key, slot]))

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

        # TODO: suppory mapping with dynamic arrays

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
        """Gets the length of dynamic and fixed arrays.
        Args:
            type_ (`AbstractType`): The array type.
            slot (int): Slot a dynamic array's length is stored at.
        Returns:
            (int): The length of the array.
        """
        val = 0
        if self.rpc:
            # The length of dynamic arrays is stored at the starting slot.
            # Convert from hexadecimal to decimal.
            val = int(
                get_storage_data(
                    self.web3, self.checksum_address, int.to_bytes(slot, 32, byteorder="big"), self.block
                ).hex(),
                16,
            )
        if isinstance(type_, ArrayType):
            if type_.is_fixed_array:
                val = int(str(type_.length))

        return val
