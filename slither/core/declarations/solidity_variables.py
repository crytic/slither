# https://solidity.readthedocs.io/en/v0.4.24/units-and-global-variables.html
from slither.core.context.context import Context
from slither.core.solidity_types import ElementaryType

SOLIDITY_VARIABLES = {"now":'uint256',
                      "this":'address',
                      'abi':'address', # to simplify the conversion, assume that abi return an address
                      'msg':'',
                      'tx':'',
                      'block':'',
                      'super':''}

SOLIDITY_VARIABLES_COMPOSED = {"block.coinbase":"address",
                               "block.difficulty":"uint256",
                               "block.gaslimit":"uint256",
                               "block.number":"uint256",
                               "block.timestamp":"uint256",
                               "block.blockhash":"uint256", # alias for blockhash. It's a call
                               "msg.data":"bytes",
                               "msg.gas":"uint256",
                               "msg.sender":"address",
                               "msg.sig":"bytes4",
                               "msg.value":"uint256",
                               "tx.gasprice":"uint256",
                               "tx.origin":"address"}


SOLIDITY_FUNCTIONS = {"gasleft()":['uint256'],
                      "assert(bool)":[],
                      "require(bool)":[],
                      "require(bool,string)":[],
                      "revert()":[],
                      "revert(string)":[],
                      "addmod(uint256,uint256,uint256)":['uint256'],
                      "mulmod(uint256,uint256,uint256)":['uint256'],
                      "keccak256()":['bytes32'],
                      "sha256()":['bytes32'],
                      "sha3()":['bytes32'],
                      "ripemd160()":['bytes32'],
                      "ecrecover(bytes32,uint8,bytes32,bytes32)":['address'],
                      "selfdestruct(address)":[],
                      "suicide(address)":[],
                      "log0(bytes32)":[],
                      "log1(bytes32,bytes32)":[],
                      "log2(bytes32,bytes32,bytes32)":[],
                      "log3(bytes32,bytes32,bytes32,bytes32)":[],
                      "blockhash(uint256)":['bytes32'],
                      # the following need a special handling
                      # as they are recognized as a SolidityVariableComposed
                      # and converted to a SolidityFunction by SlithIR
                      "this.balance()":['uint256'],
                      "abi.encode()":['bytes'],
                      "abi.encodePacked()":['bytes'],
                      "abi.encodeWithSelector()":["bytes"],
                      "abi.encodeWithSignature()":["bytes"]}

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
    return name+' returns({})'.format(','.join(SOLIDITY_FUNCTIONS[name]))

class SolidityVariable(Context):

    def __init__(self, name):
        super(SolidityVariable, self).__init__()
        self._check_name(name)
        self._name = name

    # dev function, will be removed once the code is stable
    def _check_name(self, name):
        assert name in SOLIDITY_VARIABLES

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return ElementaryType(SOLIDITY_VARIABLES[self.name])

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name

    def __hash__(self):
        return hash(self.name)

class SolidityVariableComposed(SolidityVariable):
    def __init__(self, name):
        super(SolidityVariableComposed, self).__init__(name)

    def _check_name(self, name):
        assert name in SOLIDITY_VARIABLES_COMPOSED

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return ElementaryType(SOLIDITY_VARIABLES_COMPOSED[self.name])

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class SolidityFunction:

    def __init__(self, name):
        assert name in SOLIDITY_FUNCTIONS
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def full_name(self):
        return self.name

    @property
    def return_type(self):
        return [ElementaryType(x) for x in SOLIDITY_FUNCTIONS[self.name]]

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name

    def __hash__(self):
        return hash(self.name)
