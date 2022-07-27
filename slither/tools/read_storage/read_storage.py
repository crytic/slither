import sys
import logging
from math import floor
from os import environ

from typing import Callable, Optional, Tuple, Union, List, Dict

try:
    from typing import TypedDict
except ImportError:
    # < Python 3.8
    from typing_extensions import TypedDict

try:
    from web3 import Web3
    from eth_typing.evm import ChecksumAddress
    from eth_abi import decode_single, encode_abi
    from eth_utils import keccak
    from hexbytes import HexBytes
    from .utils import (
        is_elementary,
        is_array,
        is_mapping,
        is_struct,
        is_user_defined_type,
        get_offset_value,
        get_storage_data,
        coerce_type,
    )
except ImportError:
    print("ERROR: in order to use slither-read-storage, you need to install web3")
    print("$ pip3 install web3 --user\n")
    sys.exit(-1)

try:
    from tabulate import tabulate
except ImportError:
    print("ERROR: in order to use slither-read-storage --table, you need to install tabulate")
    print("$ pip3 install tabulate --user\n")
    sys.exit(-1)

from slither.core.solidity_types.type import Type
from slither.core.solidity_types import ArrayType
from slither.core.declarations import Contract, StructureContract
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.structure_variable import StructureVariable


logging.basicConfig()
logger = logging.getLogger("Slither-read-storage")
logger.setLevel(logging.INFO)


class SlotInfo(TypedDict):
    type_string: str
    slot: int
    size: int
    offset: int
    value: Optional[Union[int, bool, str, ChecksumAddress, hex]]
    elems: Optional[TypedDict]  # same types as SlotInfo


class SlitherReadStorageException(Exception):
    pass


# pylint: disable=too-many-instance-attributes
class SlitherReadStorage:
    def __init__(self, contracts, max_depth):
        self._contracts: List[Contract] = contracts
        self._max_depth: int = max_depth
        self._log: str = ""
        self._slot_info: SlotInfo = {}
        self._target_variables = []
        self._web3: Optional[Web3] = None
        self._checksum_address: Optional[ChecksumAddress] = None
        self.storage_address: Optional[str] = None
        self.rpc: Optional[str] = None

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
    def log(self, log) -> str:
        self._log = log

    @property
    def web3(self) -> Web3:
        if not self._web3:
            self._web3 = Web3(Web3.HTTPProvider(self.rpc))
        return self._web3

    @property
    def checksum_address(self) -> ChecksumAddress:
        if not self._checksum_address:
            self._checksum_address = self.web3.toChecksumAddress(self.storage_address)
        return self._checksum_address

    @property
    def target_variables(self) -> List[Tuple[Contract, StateVariable]]:
        """Storage variables (not constant or immutable) and their associated contract."""
        return self._target_variables

    @property
    def slot_info(self) -> SlotInfo:
        """Contains the location, type, size, offset, and value of contract slots."""
        return self._slot_info

    def get_storage_layout(self) -> None:
        """Retrieves the storage layout of entire contract."""
        tmp = {}
        for contract, var in self.target_variables:
            type_ = var.type
            info = self.get_storage_slot(var, contract)
            tmp[var.name] = info

            if is_user_defined_type(type_) and is_struct(type_.type):
                tmp[var.name]["elems"] = self._all_struct_slots(var, contract)
                continue

            if is_array(type_):
                elems = self._all_array_slots(var, contract, type_, info["slot"])
                tmp[var.name]["elems"] = elems

        self._slot_info = tmp

    def get_storage_slot(
        self,
        target_variable: StateVariable,
        contract: Contract,
        **kwargs,
    ) -> Union[SlotInfo, None]:
        """Finds the storage slot of a variable in a given contract.
        Args:
            target_variable (`StateVariable`): The variable to retrieve the slot for.
            contracts (`Contract`): The contract that contains the given state variable.
        **kwargs:
            key (str): Key of a mapping or index position if an array.
            deep_key (str): Key of a mapping embedded within another mapping or
            secondary index if array.
            struct_var (str): Structure variable name.
        Returns:
            (`SlotInfo`) | None : A dictionary of the slot information.
        """

        key = kwargs.get("key", None)
        deep_key = kwargs.get("deep_key", None)
        struct_var = kwargs.get("struct_var", None)
        info = ""
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

        if is_elementary(target_variable.type):
            type_to = target_variable.type.name

        elif is_array(target_variable.type) and key:
            info, type_to, slot, size, offset = self._find_array_slot(
                target_variable, slot, key, deep_key=deep_key, struct_var=struct_var
            )
            self.log += info

        elif is_user_defined_type(target_variable.type) and struct_var:
            var_log_name = struct_var
            elems = target_variable.type.type.elems_ordered
            info, type_to, slot, size, offset = self._find_struct_var_slot(elems, slot, struct_var)
            self.log += info

        elif is_mapping(target_variable.type) and key:
            info, type_to, slot, size, offset = self._find_mapping_slot(
                target_variable, slot, key, struct_var=struct_var, deep_key=deep_key
            )
            self.log += info

        int_slot = int.from_bytes(slot, byteorder="big")
        self.log += f"\nName: {var_log_name}\nType: {type_to}\nSlot: {int_slot}\n"
        if environ.get("SILENT") is None:
            logger.info(self.log)
        self.log = ""
        if environ.get("TABLE") is None:
            return {
                "type_string": type_to,
                "slot": int_slot,
                "size": size,
                "offset": offset,
            }
        return {
            "type_string": type_to,
            "slot": int_slot,
            "size": size,
            "offset": offset,
            "struct_var": struct_var,
        }

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
            self._slot_info[f"{contract.name}.{var.name}"] = self.get_storage_slot(
                var, contract, **kwargs
            )

    def get_slot_values(self) -> SlotInfo:
        """
        Fetches the slot values and inserts them in slot info dictionary.
        Returns:
            (`SlotInfo`): The dictionary of slot info.
        """
        stack = list(self.slot_info.items())
        while stack:
            _, v = stack.pop()
            if isinstance(v, dict):
                stack.extend(v.items())
                if "slot" in v:
                    hex_bytes = get_storage_data(self.web3, self.checksum_address, v["slot"])
                    v["value"] = self.convert_value_to_type(
                        hex_bytes, v["size"], v["offset"], v["type_string"]
                    )
                    logger.info(f"\nValue: {v['value']}\n")
        return self.slot_info

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

    def print_table(self) -> None:

        tabulate_data = []

        for _, state_var in self.target_variables:
            type_ = state_var.type
            var = state_var.name
            info = self.slot_info[var]
            slot = info.get("slot")
            offset = info.get("offset")
            size = info.get("size")
            type_string = info.get("type_string")
            struct_var = info.get("struct_var")

            tabulate_data.append([slot, offset, size, type_string, var])

            if is_user_defined_type(type_) and is_struct(type_.type):
                tabulate_data.pop()
                for item in info["elems"]:
                    slot = info["elems"][item].get("slot")
                    offset = info["elems"][item].get("offset")
                    size = info["elems"][item].get("size")
                    type_string = info["elems"][item].get("type_string")
                    struct_var = info["elems"][item].get("struct_var")

                    # doesn't handle deep keys currently
                    var_name_struct_or_array_var = f"{var} -> {struct_var}"

                    tabulate_data.append(
                        [slot, offset, size, type_string, var_name_struct_or_array_var]
                    )

            if is_array(type_):
                tabulate_data.pop()
                for item in info["elems"]:
                    for key in info["elems"][item]:
                        slot = info["elems"][item][key].get("slot")
                        offset = info["elems"][item][key].get("offset")
                        size = info["elems"][item][key].get("size")
                        type_string = info["elems"][item][key].get("type_string")
                        struct_var = info["elems"][item][key].get("struct_var")

                        # doesn't handle deep keys currently
                        var_name_struct_or_array_var = f"{var}[{item}] -> {struct_var}"

                        tabulate_data.append(
                            [slot, offset, size, type_string, var_name_struct_or_array_var]
                        )

        print(
            tabulate(
                tabulate_data, headers=["slot", "offset", "size", "type", "name"], tablefmt="grid"
            )
        )

    def print_table_with_values(self) -> None:

        print("Processing, grabbing values from rpc endpoint...")
        tabulate_data = []

        for _, state_var in self.target_variables:
            type_ = state_var.type
            var = state_var.name
            info = self.slot_info[var]
            slot = info.get("slot")
            offset = info.get("offset")
            size = info.get("size")
            type_string = info.get("type_string")
            struct_var = info.get("struct_var")

            tabulate_data.append(
                [
                    slot,
                    offset,
                    size,
                    type_string,
                    var,
                    self.convert_value_to_type(
                        get_storage_data(self.web3, self.checksum_address, slot),
                        size,
                        offset,
                        type_string,
                    ),
                ]
            )

            if is_user_defined_type(type_) and is_struct(type_.type):
                tabulate_data.pop()
                for item in info["elems"]:
                    slot = info["elems"][item].get("slot")
                    offset = info["elems"][item].get("offset")
                    size = info["elems"][item].get("size")
                    type_string = info["elems"][item].get("type_string")
                    struct_var = info["elems"][item].get("struct_var")

                    # doesn't handle deep keys currently
                    var_name_struct_or_array_var = f"{var} -> {struct_var}"

                    tabulate_data.append(
                        [
                            slot,
                            offset,
                            size,
                            type_string,
                            var_name_struct_or_array_var,
                            self.convert_value_to_type(
                                get_storage_data(self.web3, self.checksum_address, slot),
                                size,
                                offset,
                                type_string,
                            ),
                        ]
                    )

            if is_array(type_):
                tabulate_data.pop()
                for item in info["elems"]:
                    for key in info["elems"][item]:
                        slot = info["elems"][item][key].get("slot")
                        offset = info["elems"][item][key].get("offset")
                        size = info["elems"][item][key].get("size")
                        type_string = info["elems"][item][key].get("type_string")
                        struct_var = info["elems"][item][key].get("struct_var")

                        # doesn't handle deep keys currently
                        var_name_struct_or_array_var = f"{var}[{item}] -> {struct_var}"

                        hex_bytes = get_storage_data(self.web3, self.checksum_address, slot)
                        tabulate_data.append(
                            [
                                slot,
                                offset,
                                size,
                                type_string,
                                var_name_struct_or_array_var,
                                self.convert_value_to_type(hex_bytes, size, offset, type_string),
                            ]
                        )

        print(
            tabulate(
                tabulate_data,
                headers=["slot", "offset", "size", "type", "name", "value"],
                tablefmt="grid",
            )
        )

    @staticmethod
    def _find_struct_var_slot(
        elems: List[StructureVariable], slot: bytes, struct_var: str
    ) -> Tuple[str, str, bytes, int, int]:
        """Finds the slot of a structure variable.
        Args:
            elems (List[StructureVariable]): Ordered list of structure variables.
            slot (bytes): The slot of the struct to begin searching at.
            struct_var (str): The target structure variable.
        Returns:
            info (str): Info about the target variable to log.
            type_to (str): The type of the target variable.
            slot (bytes): The storage location of the target variable.
            size (int): The size (in bits) of the target variable.
            offset (int): The size of other variables that share the same slot.
        """
        slot = int.from_bytes(slot, "big")
        offset = 0
        for var in elems:
            size = var.type.size
            if offset >= 256:
                slot += 1
                offset = 0
            if struct_var == var.name:
                type_to = var.type.name
                break  # found struct var
            offset += size

        slot = int.to_bytes(slot, 32, byteorder="big")
        info = f"\nStruct Variable: {struct_var}"
        return info, type_to, slot, size, offset

    # pylint: disable=too-many-branches
    @staticmethod
    def _find_array_slot(
        target_variable: StateVariable,
        slot: bytes,
        key: int,
        deep_key: int = None,
        struct_var: str = None,
    ) -> Tuple[str, str, bytes]:
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
        """
        info = f"\nKey: {key}"
        offset = 0
        size = 256

        if is_array(
            target_variable.type.type
        ):  # multidimensional array uint[i][], , uint[][i], or uint[][]
            size = target_variable.type.type.type.size
            type_to = target_variable.type.type.type.name

            if target_variable.type.is_fixed_array:  # uint[][i]
                slot_int = int.from_bytes(slot, "big") + int(key)
            else:
                slot = keccak(slot)
                key = int(key)
                if target_variable.type.type.is_fixed_array:  # arr[i][]
                    key *= int(str(target_variable.type.type.length))
                slot_int = int.from_bytes(slot, "big") + key

            if not deep_key:
                return info, type_to, int.to_bytes(slot_int, 32, "big"), size, offset

            info += f"\nDeep Key: {deep_key}"
            if target_variable.type.type.is_dynamic_array:  # uint[][]
                # keccak256(keccak256(slot) + index) + floor(j / floor(256 / size))
                slot = keccak(int.to_bytes(slot_int, 32, "big"))
                slot_int = int.from_bytes(slot, "big")

            # keccak256(slot) + index + floor(j / floor(256 / size))
            slot_int += floor(int(deep_key) / floor(256 / size))  # uint[i][]

        elif target_variable.type.is_fixed_array:
            slot_int = int.from_bytes(slot, "big") + int(key)
            if is_user_defined_type(target_variable.type.type):  # struct[i]
                type_to = target_variable.type.type.type.name
                if not struct_var:
                    return info, type_to, int.to_bytes(slot_int, 32, "big"), size, offset
                elems = target_variable.type.type.type.elems_ordered
                slot = int.to_bytes(slot_int, 32, byteorder="big")
                info_tmp, type_to, slot, size, offset = SlitherReadStorage._find_struct_var_slot(
                    elems, slot, struct_var
                )
                info += info_tmp

            else:
                type_to = target_variable.type.type.name
                size = target_variable.type.type.size  # bits

        elif is_user_defined_type(target_variable.type.type):  # struct[]
            slot = keccak(slot)
            slot_int = int.from_bytes(slot, "big") + int(key)
            type_to = target_variable.type.type.type.name
            if not struct_var:
                return info, type_to, int.to_bytes(slot_int, 32, "big"), size, offset
            elems = target_variable.type.type.type.elems_ordered
            slot = int.to_bytes(slot_int, 32, byteorder="big")
            info_tmp, type_to, slot, size, offset = SlitherReadStorage._find_struct_var_slot(
                elems, slot, struct_var
            )
            info += info_tmp

        else:
            slot = keccak(slot)
            slot_int = int.from_bytes(slot, "big") + int(key)
            type_to = target_variable.type.type.name
            size = target_variable.type.type.size  # bits

        slot = int.to_bytes(slot_int, 32, byteorder="big")

        return info, type_to, slot, size, offset

    @staticmethod
    def _find_mapping_slot(
        target_variable: StateVariable,
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
            type_to (bytes): The type of the target variable.
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

        key_type = target_variable.type.type_from.name
        assert key
        if "int" in key_type:  # without this eth_utils encoding fails
            key = int(key)
        key = coerce_type(key_type, key)
        slot = keccak(encode_abi([key_type, "uint256"], [key, decode_single("uint256", slot)]))

        if is_user_defined_type(target_variable.type.type_to) and is_struct(
            target_variable.type.type_to.type
        ):  # mapping(elem => struct)
            assert struct_var
            elems = target_variable.type.type_to.type.elems_ordered
            info_tmp, type_to, slot, size, offset = SlitherReadStorage._find_struct_var_slot(
                elems, slot, struct_var
            )
            info += info_tmp

        elif is_mapping(target_variable.type.type_to):  # mapping(elem => mapping(elem => ???))
            assert deep_key
            key_type = target_variable.type.type_to.type_from.name
            if "int" in key_type:  # without this eth_utils encoding fails
                deep_key = int(deep_key)

            # If deep map, will be keccak256(abi.encode(key1, keccak256(abi.encode(key0, uint(slot)))))
            slot = keccak(encode_abi([key_type, "bytes32"], [deep_key, slot]))

            # mapping(elem => mapping(elem => elem))
            type_to = target_variable.type.type_to.type_to.type
            byte_size, _ = target_variable.type.type_to.type_to.storage_size
            size = byte_size * 8  # bits
            offset = 0

            if is_user_defined_type(target_variable.type.type_to.type_to) and is_struct(
                target_variable.type.type_to.type_to.type
            ):  # mapping(elem => mapping(elem => struct))
                assert struct_var
                elems = target_variable.type.type_to.type_to.type.elems_ordered
                # If map struct, will be bytes32(uint256(keccak256(abi.encode(key1, keccak256(abi.encode(key0, uint(slot)))))) + structFieldDepth);
                info_tmp, type_to, slot, size, offset = SlitherReadStorage._find_struct_var_slot(
                    elems, slot, struct_var
                )
                info += info_tmp

        # TODO: suppory mapping with dynamic arrays

        else:  # mapping(elem => elem)
            type_to = target_variable.type.type_to.name  # the value's elementary type
            byte_size, _ = target_variable.type.type_to.storage_size
            size = byte_size * 8  # bits

        return info, type_to, slot, size, offset

    @staticmethod
    def get_variable_info(
        contract: Contract, target_variable: StateVariable
    ) -> Tuple[int, int, int, str]:
        """Return slot, size, offset, and type."""
        type_to = str(target_variable.type)
        byte_size, _ = target_variable.type.storage_size
        size = byte_size * 8  # bits
        (int_slot, offset) = contract.compilation_unit.storage_layout_of(contract, target_variable)
        offset *= 8  # bits
        if environ.get("SILENT") is None:
            logger.info(
                f"\nContract '{contract.name}'\n{target_variable.canonical_name} with type {target_variable.type} is located at slot: {int_slot}\n"
            )

        return int_slot, size, offset, type_to

    @staticmethod
    def convert_value_to_type(
        hex_bytes: HexBytes, size: int, offset: int, type_to: str
    ) -> Union[int, bool, str, ChecksumAddress, hex]:
        """Convert slot data to type representation."""
        # Account for storage packing
        offset_hex_bytes = get_offset_value(hex_bytes, offset, size)
        try:
            value = coerce_type(type_to, offset_hex_bytes)
        except ValueError:
            return coerce_type("int", offset_hex_bytes)

        return value

    def _all_struct_slots(
        self, var: Union[StructureVariable, StructureContract], contract: Contract, key=None
    ) -> Dict[str, SlotInfo]:
        """Retrieves all members of a struct."""
        if isinstance(var.type.type, StructureContract):
            struct_elems = var.type.type.elems_ordered
        else:
            struct_elems = var.type.type.type.elems_ordered
        data = {}
        for elem in struct_elems:
            info = self.get_storage_slot(
                var,
                contract,
                key=key,
                struct_var=elem.name,
            )
            data[elem.name] = info

        return data

    def _all_array_slots(
        self, var: ArrayType, contract: Contract, type_: Type, slot: int
    ) -> Dict[int, SlotInfo]:
        """Retrieves all members of an array."""
        array_length = self._get_array_length(type_, slot)
        elems = {}
        if is_user_defined_type(type_.type):
            for i in range(min(array_length, self.max_depth)):
                elems[i] = self._all_struct_slots(var, contract, key=str(i))
                continue

        else:
            for i in range(min(array_length, self.max_depth)):
                info = self.get_storage_slot(
                    var,
                    contract,
                    key=str(i),
                )
                elems[i] = info

                if is_array(type_.type):  # multidimensional array
                    array_length = self._get_array_length(type_.type, info["slot"])

                    elems[i]["elems"] = {}
                    for j in range(min(array_length, self.max_depth)):
                        info = self.get_storage_slot(
                            var,
                            contract,
                            key=str(i),
                            deep_key=str(j),
                        )

                        elems[i]["elems"][j] = info
        return elems

    def _get_array_length(self, type_: Type, slot: int = None) -> int:
        """Gets the length of dynamic and fixed arrays.
        Args:
            type_ (`Type`): The array type.
            slot (int, optional): Slot a dynamic array's length is stored at.
        Returns:
            (int): The length of the array.
        """
        val = 0
        if self.rpc:
            # The length of dynamic arrays is stored at the starting slot.
            # Convert from hexadecimal to decimal.
            val = int(get_storage_data(self.web3, self.checksum_address, slot).hex(), 16)
        if is_array(type_):
            if type_.is_fixed_array:
                val = int(str(type_.length))

        return val
