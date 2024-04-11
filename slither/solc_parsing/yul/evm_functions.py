from slither.core.declarations.solidity_variables import SOLIDITY_FUNCTIONS
from slither.core.expressions import BinaryOperationType, UnaryOperationType

# taken from https://github.com/ethereum/solidity/blob/e11b9ed9f2c254bc894d844c0a64a0eb76bbb4fd/libevmasm/Instruction.cpp#L184
evm_opcodes = [
    "STOP",
    "ADD",
    "SUB",
    "MUL",
    "DIV",
    "SDIV",
    "MOD",
    "SMOD",
    "EXP",
    "NOT",
    "LT",
    "GT",
    "SLT",
    "SGT",
    "EQ",
    "ISZERO",
    "AND",
    "OR",
    "XOR",
    "BYTE",
    "SHL",
    "SHR",
    "SAR",
    "ADDMOD",
    "MULMOD",
    "SIGNEXTEND",
    "KECCAK256",
    "ADDRESS",
    "BALANCE",
    "ORIGIN",
    "CALLER",
    "CALLVALUE",
    "CALLDATALOAD",
    "CALLDATASIZE",
    "CALLDATACOPY",
    "CODESIZE",
    "CODECOPY",
    "GASPRICE",
    "EXTCODESIZE",
    "EXTCODECOPY",
    "RETURNDATASIZE",
    "RETURNDATACOPY",
    "MCOPY",
    "EXTCODEHASH",
    "BLOCKHASH",
    "COINBASE",
    "TIMESTAMP",
    "NUMBER",
    "DIFFICULTY",
    "PREVRANDAO",
    "GASLIMIT",
    "CHAINID",
    "SELFBALANCE",
    "BASEFEE",
    "BLOBHASH",
    "BLOBBASEFEE",
    "POP",
    "MLOAD",
    "MSTORE",
    "MSTORE8",
    "SLOAD",
    "SSTORE",
    "TLOAD",
    "TSTORE",
    "JUMP",
    "JUMPI",
    "PC",
    "MSIZE",
    "GAS",
    "JUMPDEST",
    "PUSH1",
    "PUSH2",
    "PUSH3",
    "PUSH4",
    "PUSH5",
    "PUSH6",
    "PUSH7",
    "PUSH8",
    "PUSH9",
    "PUSH10",
    "PUSH11",
    "PUSH12",
    "PUSH13",
    "PUSH14",
    "PUSH15",
    "PUSH16",
    "PUSH17",
    "PUSH18",
    "PUSH19",
    "PUSH20",
    "PUSH21",
    "PUSH22",
    "PUSH23",
    "PUSH24",
    "PUSH25",
    "PUSH26",
    "PUSH27",
    "PUSH28",
    "PUSH29",
    "PUSH30",
    "PUSH31",
    "PUSH32",
    "DUP1",
    "DUP2",
    "DUP3",
    "DUP4",
    "DUP5",
    "DUP6",
    "DUP7",
    "DUP8",
    "DUP9",
    "DUP10",
    "DUP11",
    "DUP12",
    "DUP13",
    "DUP14",
    "DUP15",
    "DUP16",
    "SWAP1",
    "SWAP2",
    "SWAP3",
    "SWAP4",
    "SWAP5",
    "SWAP6",
    "SWAP7",
    "SWAP8",
    "SWAP9",
    "SWAP10",
    "SWAP11",
    "SWAP12",
    "SWAP13",
    "SWAP14",
    "SWAP15",
    "SWAP16",
    "LOG0",
    "LOG1",
    "LOG2",
    "LOG3",
    "LOG4",
    "CREATE",
    "CALL",
    "CALLCODE",
    "STATICCALL",
    "RETURN",
    "DELEGATECALL",
    "CREATE2",
    "REVERT",
    "INVALID",
    "SELFDESTRUCT",
]

yul_funcs = [
    "datasize",
    "dataoffset",
    "datacopy",
    "setimmutable",
    "loadimmutable",
]

builtins = [
    x.lower()
    for x in evm_opcodes
    if not (
        x.startswith("PUSH")
        or x.startswith("SWAP")
        or x.startswith("DUP")
        or x == "JUMP"
        or x == "JUMPI"
        or x == "JUMPDEST"
    )
] + yul_funcs

# "identifier": [input_count, output_count]
function_args = {
    "byte": [2, 1],
    "addmod": [3, 1],
    "mulmod": [3, 1],
    "signextend": [2, 1],
    "keccak256": [2, 1],
    "pc": [0, 1],
    "pop": [1, 0],
    "mload": [1, 1],
    "mstore": [2, 0],
    "mstore8": [2, 0],
    "sload": [1, 1],
    "sstore": [2, 0],
    "tload": [1, 1],
    "tstore": [2, 0],
    "msize": [1, 1],
    "gas": [0, 1],
    "address": [0, 1],
    "balance": [1, 1],
    "selfbalance": [0, 1],
    "basefee": [0, 1],
    "blobhash": [1, 1],
    "blobbasefee": [0, 1],
    "caller": [0, 1],
    "callvalue": [0, 1],
    "calldataload": [1, 1],
    "calldatasize": [0, 1],
    "calldatacopy": [3, 0],
    "codesize": [0, 1],
    "codecopy": [3, 0],
    "extcodesize": [1, 1],
    "extcodecopy": [4, 0],
    "returndatasize": [0, 1],
    "returndatacopy": [3, 0],
    "mcopy": [3, 0],
    "extcodehash": [1, 1],
    "create": [3, 1],
    "create2": [4, 1],
    "call": [7, 1],
    "callcode": [7, 1],
    "delegatecall": [6, 1],
    "staticcall": [6, 1],
    "return": [2, 0],
    "revert": [2, 0],
    "selfdestruct": [1, 0],
    "invalid": [0, 0],
    "log0": [2, 0],
    "log1": [3, 0],
    "log2": [4, 0],
    "log3": [5, 0],
    "log4": [6, 0],
    "chainid": [0, 1],
    "origin": [0, 1],
    "gasprice": [0, 1],
    "blockhash": [1, 1],
    "coinbase": [0, 1],
    "timestamp": [0, 1],
    "number": [0, 1],
    "difficulty": [0, 1],
    "prevrandao": [0, 1],
    "gaslimit": [0, 1],
}


def format_function_descriptor(name: str) -> str:
    if name not in function_args:
        return name + "()"

    return name + "(" + ",".join(["uint256"] * function_args[name][0]) + ")"


for k, v in function_args.items():
    SOLIDITY_FUNCTIONS[format_function_descriptor(k)] = ["uint256"] * v[1]

unary_ops = {
    "not": UnaryOperationType.TILD,
    "iszero": UnaryOperationType.BANG,
}

binary_ops = {
    "add": BinaryOperationType.ADDITION,
    "sub": BinaryOperationType.SUBTRACTION,
    "mul": BinaryOperationType.MULTIPLICATION,
    "div": BinaryOperationType.DIVISION,
    "sdiv": BinaryOperationType.DIVISION_SIGNED,
    "mod": BinaryOperationType.MODULO,
    "smod": BinaryOperationType.MODULO_SIGNED,
    "exp": BinaryOperationType.POWER,
    "lt": BinaryOperationType.LESS,
    "gt": BinaryOperationType.GREATER,
    "slt": BinaryOperationType.LESS_SIGNED,
    "sgt": BinaryOperationType.GREATER_SIGNED,
    "eq": BinaryOperationType.EQUAL,
    "and": BinaryOperationType.AND,
    "or": BinaryOperationType.OR,
    "xor": BinaryOperationType.CARET,
    "shl": BinaryOperationType.LEFT_SHIFT,
    "shr": BinaryOperationType.RIGHT_SHIFT,
    "sar": BinaryOperationType.RIGHT_SHIFT_ARITHMETIC,
}


class YulBuiltin:  # pylint: disable=too-few-public-methods
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name
