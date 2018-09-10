# https://solidity.readthedocs.io/en/v0.4.24/units-and-global-variables.html


SOLIDITY_VARIABLES = ["block", "msg", "now", "tx", "this", "super", 'abi']

SOLIDITY_VARIABLES_COMPOSED = ["block.coinbase", "block.difficulty", "block.gaslimit", "block.number", "block.timestamp", "msg.data", "msg.gas", "msg.sender", "msg.sig", "msg.value", "tx.gasprice", "tx.origin"]

SOLIDITY_FUNCTIONS = ["gasleft()", "assert(bool)", "require(bool)", "require(bool,string)", "revert()", "revert(string)", "addmod(uint256,uint256,uint256)", "mulmod(uint256,uint256,uint256)", "keccak256()", "sha256()", "sha3()", "ripemd160()", "ecrecover(bytes32,uint8,bytes32,bytes32)", "selfdestruct(address)", "suicide(address)", "log0(bytes32)", "log1(bytes32,bytes32)", "log2(bytes32,bytes32,bytes32)", "log3(bytes32,bytes32,bytes32,bytes32)", "blockhash(uint256)"]

class SolidityVariable:

    def __init__(self, name):
        assert name in SOLIDITY_VARIABLES
        self._name = name

    @property
    def name(self):
        return self._name

    def __str__(self):
        return self._name

class SolidityVariableComposed(SolidityVariable):
    def __init__(self, name):
        assert name in SOLIDITY_VARIABLES_COMPOSED
        self._name = name

    @property
    def name(self):
        return self._name

    def __str__(self):
        return self._name



class SolidityFunction:

    def __init__(self, name):
        assert name in SOLIDITY_FUNCTIONS
        self._name = name

    @property
    def name(self):
        return self._name

    def __str__(self):
        return self._name
