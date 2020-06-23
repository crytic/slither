from enum import Enum
from typing import NamedTuple


class PropertyType(Enum):
    CODE_QUALITY = 1
    LOW_SEVERITY = 2
    MEDIUM_SEVERITY = 3
    HIGH_SEVERITY = 4


class PropertyReturn(Enum):
    SUCCESS = 1
    FAIL_OR_THROW = 2
    FAIL = 3
    THROW = 4


class PropertyCaller(Enum):
    OWNER = 1
    SENDER = 2
    ATTACKER = 3
    ALL = 4  # If all the actors should call the function. Typically if the test uses msg.sender
    ANY = 5  # If the caller does not matter


class Property(NamedTuple):
    name: str
    content: str
    type: PropertyType
    return_type: PropertyReturn
    is_unit_test: bool
    caller: PropertyCaller  # Only for unit tests. Echidna will try all the callers
    is_property_test: bool
    description: str


def property_to_solidity(p: Property):
    return f"\tfunction {p.name} public returns(bool){{{p.content}\n\t}}\n"
