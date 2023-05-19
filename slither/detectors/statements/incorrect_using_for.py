from typing import List

from slither.core.declarations import Contract, Structure, Enum
from slither.core.declarations.using_for_top_level import UsingForTopLevel
from slither.core.solidity_types import (
    UserDefinedType,
    Type,
    ElementaryType,
    TypeAlias,
    MappingType,
    ArrayType,
)
from slither.core.solidity_types.elementary_type import Uint, Int, Byte
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


def _is_correctly_used(type_: Type, library: Contract) -> bool:
    """
    Checks if a `using library for type_` statement is used correctly (that is, does library contain any function
    with type_ as the first argument).
    """
    for f in library.functions:
        if len(f.parameters) == 0:
            continue
        if f.parameters[0].type and not _implicitly_convertible_to(type_, f.parameters[0].type):
            continue
        return True
    return False


def _implicitly_convertible_to(type1: Type, type2: Type) -> bool:
    """
    Returns True if type1 may be implicitly converted to type2.
    """
    if isinstance(type1, TypeAlias) or isinstance(type2, TypeAlias):
        if isinstance(type1, TypeAlias) and isinstance(type2, TypeAlias):
            return type1.type == type2.type
        return False

    if isinstance(type1, UserDefinedType) and isinstance(type2, UserDefinedType):
        if isinstance(type1.type, Contract) and isinstance(type2.type, Contract):
            return _implicitly_convertible_to_for_contracts(type1.type, type2.type)

        if isinstance(type1.type, Structure) and isinstance(type2.type, Structure):
            return type1.type.canonical_name == type2.type.canonical_name

        if isinstance(type1.type, Enum) and isinstance(type2.type, Enum):
            return type1.type.canonical_name == type2.type.canonical_name

    if isinstance(type1, ElementaryType) and isinstance(type2, ElementaryType):
        return _implicitly_convertible_to_for_elementary_types(type1, type2)

    if isinstance(type1, MappingType) and isinstance(type2, MappingType):
        return _implicitly_convertible_to_for_mappings(type1, type2)

    if isinstance(type1, ArrayType) and isinstance(type2, ArrayType):
        return _implicitly_convertible_to_for_arrays(type1, type2)

    return False


def _implicitly_convertible_to_for_arrays(type1: ArrayType, type2: ArrayType) -> bool:
    """
    Returns True if type1 may be implicitly converted to type2.
    """
    return _implicitly_convertible_to(type1.type, type2.type)


def _implicitly_convertible_to_for_mappings(type1: MappingType, type2: MappingType) -> bool:
    """
    Returns True if type1 may be implicitly converted to type2.
    """
    return type1.type_from == type2.type_from and type1.type_to == type2.type_to


def _implicitly_convertible_to_for_elementary_types(
    type1: ElementaryType, type2: ElementaryType
) -> bool:
    """
    Returns True if type1 may be implicitly converted to type2.
    """
    if type1.type == "bool" and type2.type == "bool":
        return True
    if type1.type == "string" and type2.type == "string":
        return True
    if type1.type == "bytes" and type2.type == "bytes":
        return True
    if type1.type == "address" and type2.type == "address":
        return _implicitly_convertible_to_for_addresses(type1, type2)
    if type1.type in Uint and type2.type in Uint:
        return _implicitly_convertible_to_for_uints(type1, type2)
    if type1.type in Int and type2.type in Int:
        return _implicitly_convertible_to_for_ints(type1, type2)
    if (
        type1.type != "bytes"
        and type2.type != "bytes"
        and type1.type in Byte
        and type2.type in Byte
    ):
        return _implicitly_convertible_to_for_bytes(type1, type2)
    return False


def _implicitly_convertible_to_for_bytes(type1: ElementaryType, type2: ElementaryType) -> bool:
    """
    Returns True if type1 may be implicitly converted to type2 assuming they are both bytes.
    """
    assert type1.type in Byte and type2.type in Byte
    assert type1.size is not None
    assert type2.size is not None

    return type1.size <= type2.size


def _implicitly_convertible_to_for_addresses(type1: ElementaryType, type2: ElementaryType) -> bool:
    """
    Returns True if type1 may be implicitly converted to type2 assuming they are both addresses.
    """
    assert type1.type == "address" and type2.type == "address"
    # payable attribute to be implemented; for now, always return True
    return True


def _implicitly_convertible_to_for_ints(type1: ElementaryType, type2: ElementaryType) -> bool:
    """
    Returns True if type1 may be implicitly converted to type2 assuming they are both ints.
    """
    assert type1.type in Int and type2.type in Int
    assert type1.size is not None
    assert type2.size is not None

    return type1.size <= type2.size


def _implicitly_convertible_to_for_uints(type1: ElementaryType, type2: ElementaryType) -> bool:
    """
    Returns True if type1 may be implicitly converted to type2 assuming they are both uints.
    """
    assert type1.type in Uint and type2.type in Uint
    assert type1.size is not None
    assert type2.size is not None

    return type1.size <= type2.size


def _implicitly_convertible_to_for_contracts(contract1: Contract, contract2: Contract) -> bool:
    """
    Returns True if contract1 may be implicitly converted to contract2.
    """
    return contract1 == contract2 or contract2 in contract1.inheritance


class IncorrectUsingFor(AbstractDetector):
    """
    Detector for incorrect using-for statement usage.
    """

    ARGUMENT = "incorrect-using-for"
    HELP = "Detects using-for statement usage when no function from a given library matches a given type"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-using-for-usage"

    WIKI_TITLE = "Incorrect usage of using-for statement"
    WIKI_DESCRIPTION = (
        "In Solidity, it is possible to use libraries for certain types, by the `using-for` statement "
        "(`using <library> for <type>`). However, the Solidity compiler doesn't check whether a given "
        "library has at least one function matching a given type. If it doesn't, such a statement has "
        "no effect and may be confusing. "
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
    ```solidity
    library L {
        function f(bool) public pure {}
    }
    
    using L for uint;
    ```
    Such a code will compile despite the fact that `L` has no function with `uint` as its first argument."""
    # endregion wiki_exploit_scenario
    WIKI_RECOMMENDATION = (
        "Make sure that the libraries used in `using-for` statements have at least one function "
        "matching a type used in these statements. "
    )

    def _append_result(
        self, results: List[Output], uf: UsingForTopLevel, type_: Type, library: Contract
    ) -> None:
        info: DETECTOR_INFO = [
            f"using-for statement at {uf.source_mapping} is incorrect - no matching function for {type_} found in ",
            library,
            ".\n",
        ]
        res = self.generate_result(info)
        results.append(res)

    def _detect(self) -> List[Output]:
        results: List[Output] = []

        for uf in self.compilation_unit.using_for_top_level:
            # UsingForTopLevel.using_for is a dict with a single entry, which is mapped to a list of functions/libraries
            # the following code extracts the type from using-for and skips using-for statements with functions
            type_ = list(uf.using_for.keys())[0]
            for lib_or_fcn in uf.using_for[type_]:
                # checking for using-for with functions is already performed by the compiler; we only consider libraries
                if isinstance(lib_or_fcn, UserDefinedType):
                    lib_or_fcn_type = lib_or_fcn.type
                    if (
                        isinstance(type_, Type)
                        and isinstance(lib_or_fcn_type, Contract)
                        and not _is_correctly_used(type_, lib_or_fcn_type)
                    ):
                        self._append_result(results, uf, type_, lib_or_fcn_type)

        return results
