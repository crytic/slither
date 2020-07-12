import itertools
from typing import Optional, Tuple

from slither.core.solidity_types.type import Type


# see https://solidity.readthedocs.io/en/v0.4.24/miscellaneous.html?highlight=grammar

Int = [
    "int",
    "int8",
    "int16",
    "int24",
    "int32",
    "int40",
    "int48",
    "int56",
    "int64",
    "int72",
    "int80",
    "int88",
    "int96",
    "int104",
    "int112",
    "int120",
    "int128",
    "int136",
    "int144",
    "int152",
    "int160",
    "int168",
    "int176",
    "int184",
    "int192",
    "int200",
    "int208",
    "int216",
    "int224",
    "int232",
    "int240",
    "int248",
    "int256",
]

Uint = [
    "uint",
    "uint8",
    "uint16",
    "uint24",
    "uint32",
    "uint40",
    "uint48",
    "uint56",
    "uint64",
    "uint72",
    "uint80",
    "uint88",
    "uint96",
    "uint104",
    "uint112",
    "uint120",
    "uint128",
    "uint136",
    "uint144",
    "uint152",
    "uint160",
    "uint168",
    "uint176",
    "uint184",
    "uint192",
    "uint200",
    "uint208",
    "uint216",
    "uint224",
    "uint232",
    "uint240",
    "uint248",
    "uint256",
]

Byte = [
    "byte",
    "bytes",
    "bytes1",
    "bytes2",
    "bytes3",
    "bytes4",
    "bytes5",
    "bytes6",
    "bytes7",
    "bytes8",
    "bytes9",
    "bytes10",
    "bytes11",
    "bytes12",
    "bytes13",
    "bytes14",
    "bytes15",
    "bytes16",
    "bytes17",
    "bytes18",
    "bytes19",
    "bytes20",
    "bytes21",
    "bytes22",
    "bytes23",
    "bytes24",
    "bytes25",
    "bytes26",
    "bytes27",
    "bytes28",
    "bytes29",
    "bytes30",
    "bytes31",
    "bytes32",
]

# https://solidity.readthedocs.io/en/v0.4.24/types.html#fixed-point-numbers
M = list(range(8, 257, 8))
N = list(range(0, 81))
MN = list(itertools.product(M, N))

Fixed = ["fixed{}x{}".format(m, n) for (m, n) in MN] + ["fixed"]
Ufixed = ["ufixed{}x{}".format(m, n) for (m, n) in MN] + ["ufixed"]

ElementaryTypeName = ["address", "bool", "string", "var"] + Int + Uint + Byte + Fixed + Ufixed


class NonElementaryType(Exception):
    pass


class ElementaryType(Type):
    def __init__(self, t):
        if t not in ElementaryTypeName:
            raise NonElementaryType
        super(ElementaryType, self).__init__()
        if t == "uint":
            t = "uint256"
        elif t == "int":
            t = "int256"
        elif t == "byte":
            t = "bytes1"
        self._type = t

    @property
    def type(self) -> str:
        return self._type

    @property
    def name(self) -> str:
        return self.type

    @property
    def size(self) -> Optional[int]:
        """
            Return the size in bits
            Return None if the size is not known
        Returns:
            int
        """
        t = self._type
        if t.startswith("uint"):
            return int(t[len("uint") :])
        if t.startswith("int"):
            return int(t[len("int") :])
        if t == "bool":
            return int(8)
        if t == "address":
            return int(160)
        if t.startswith("bytes"):
            return int(t[len("bytes") :])
        return None

    @property
    def storage_size(self) -> Tuple[int, bool]:
        if self._type == 'string' or self._type == 'bytes':
            return 32, True

        return int(self.size / 8), False

    def __str__(self):
        return self._type

    def __eq__(self, other):
        if not isinstance(other, ElementaryType):
            return False
        return self.type == other.type

    def __hash__(self):
        return hash(str(self))
