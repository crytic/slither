# https://solidity.readthedocs.io/en/v0.4.24/units-and-global-variables.html
from typing import List, Dict, Union, TYPE_CHECKING

from slither.core.context.context import Context
from slither.core.declarations.custom_error import CustomError
from slither.core.solidity_types import ElementaryType, TypeInformation
from slither.exceptions import SlitherException

if TYPE_CHECKING:
    pass

SOLIDITY_VARIABLES = {
    "now": "uint256",
    "this": "address",
    "abi": "address",  # to simplify the conversion, assume that abi return an address
    "msg": "",
    "tx": "",
    "block": "",
    "super": "",
}

SOLIDITY_VARIABLES_COMPOSED = {
    "block.basefee": "uint",
    "block.coinbase": "address",
    "block.difficulty": "uint256",
    "block.gaslimit": "uint256",
    "block.number": "uint256",
    "block.timestamp": "uint256",
    "block.blockhash": "uint256",  # alias for blockhash. It's a call
    "block.chainid": "uint256",
    "msg.data": "bytes",
    "msg.gas": "uint256",
    "msg.sender": "address",
    "msg.sig": "bytes4",
    "msg.value": "uint256",
    "tx.gasprice": "uint256",
    "tx.origin": "address",
}

SOLIDITY_FUNCTIONS: Dict[str, List[str]] = {
    "gasleft()": ["uint256"],
    "assert(bool)": [],
    "require(bool)": [],
    "require(bool,string)": [],
    "revert()": [],
    "revert(string)": [],
    "revert ": [],
    "addmod(uint256,uint256,uint256)": ["uint256"],
    "mulmod(uint256,uint256,uint256)": ["uint256"],
    "keccak256()": ["bytes32"],
    "keccak256(bytes)": ["bytes32"],  # Solidity 0.5
    "sha256()": ["bytes32"],
    "sha256(bytes)": ["bytes32"],  # Solidity 0.5
    "sha3()": ["bytes32"],
    "ripemd160()": ["bytes32"],
    "ripemd160(bytes)": ["bytes32"],  # Solidity 0.5
    "ecrecover(bytes32,uint8,bytes32,bytes32)": ["address"],
    "selfdestruct(address)": [],
    "suicide(address)": [],
    "log0(bytes32)": [],
    "log1(bytes32,bytes32)": [],
    "log2(bytes32,bytes32,bytes32)": [],
    "log3(bytes32,bytes32,bytes32,bytes32)": [],
    "blockhash(uint256)": ["bytes32"],
    # the following need a special handling
    # as they are recognized as a SolidityVariableComposed
    # and converted to a SolidityFunction by SlithIR
    "this.balance()": ["uint256"],
    "abi.encode()": ["bytes"],
    "abi.encodePacked()": ["bytes"],
    "abi.encodeWithSelector()": ["bytes"],
    "abi.encodeWithSignature()": ["bytes"],
    "bytes.concat()": ["bytes"],
    # abi.decode returns an a list arbitrary types
    "abi.decode()": [],
    "type(address)": [],
    "type()": [],  # 0.6.8 changed type(address) to type()
    # The following are conversion from address.something
    "balance(address)": ["uint256"],
    "code(address)": ["bytes"],
    "codehash(address)": ["bytes32"],
}


def solidity_function_signature(name):
    """
        Return the function signature (containing the return value)
        It is useful if a solidity function is used as a pointer
        (see exoressionParsing.find_variable documentation)
    Args:
        name(str):
    Returns:
        str
    """
    return name + " returns({})".format(",".join(SOLIDITY_FUNCTIONS[name]))


class SolidityVariable(Context):
    def __init__(self, name: str):
        super().__init__()
        self._check_name(name)
        self._name = name

    # dev function, will be removed once the code is stable
    def _check_name(self, name: str):  # pylint: disable=no-self-use
        assert name in SOLIDITY_VARIABLES or name.endswith("_slot") or name.endswith("_offset")

    @property
    def state_variable(self):
        if self._name.endswith("_slot"):
            return self._name[:-5]
        if self._name.endswith("_offset"):
            return self._name[:-7]
        to_log = f"Incorrect YUL parsing. {self} is not a solidity variable that can be seen as a state variable"
        raise SlitherException(to_log)

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> ElementaryType:
        return ElementaryType(SOLIDITY_VARIABLES[self.name])

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class SolidityVariableComposed(SolidityVariable):
    def _check_name(self, name: str):
        assert name in SOLIDITY_VARIABLES_COMPOSED

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> ElementaryType:
        return ElementaryType(SOLIDITY_VARIABLES_COMPOSED[self.name])

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class SolidityFunction:
    # Non standard handling of type(address). This function returns an undefined object
    # The type is dynamic
    # https://solidity.readthedocs.io/en/latest/units-and-global-variables.html#type-information
    # As a result, we set return_type during the Ir conversion

    def __init__(self, name: str):
        assert name in SOLIDITY_FUNCTIONS
        self._name = name
        # Can be TypeInformation if type(address) is used
        self._return_type: List[Union[TypeInformation, ElementaryType]] = [
            ElementaryType(x) for x in SOLIDITY_FUNCTIONS[self.name]
        ]

    @property
    def name(self) -> str:
        return self._name

    @property
    def full_name(self) -> str:
        return self.name

    @property
    def return_type(self) -> List[Union[TypeInformation, ElementaryType]]:
        return self._return_type

    @return_type.setter
    def return_type(self, r: List[Union[TypeInformation, ElementaryType]]):
        self._return_type = r

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class SolidityCustomRevert(SolidityFunction):
    def __init__(self, custom_error: CustomError):  # pylint: disable=super-init-not-called
        self._name = "revert " + custom_error.solidity_signature
        self._custom_error = custom_error
        self._return_type: List[Union[TypeInformation, ElementaryType]] = []

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.name == other.name
            and self._custom_error == other._custom_error
        )

    def __hash__(self):
        return hash(hash(self.name) + hash(self._custom_error))
