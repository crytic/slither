# https://solidity.readthedocs.io/en/v0.4.24/units-and-global-variables.html
from slither.core.context.context import Context

SOLIDITY_VARIABLES = ["block", "msg", "now", "tx", "this", "super", 'abi']

SOLIDITY_VARIABLES_COMPOSED = ["block.coinbase",
                               "block.difficulty",
                               "block.gaslimit",
                               "block.number",
                               "block.timestamp",
                               "block.blockhash", # alias for blockhash. It's a call
                               "msg.data",
                               "msg.gas",
                               "msg.sender",
                               "msg.sig",
                               "msg.value",
                               "tx.gasprice",
                               "tx.origin",
                               "this.balance"]


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
                      "blockhash(uint256)":['bytes32']}

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

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name

    def __hash__(self):
        return hash(self.name)
