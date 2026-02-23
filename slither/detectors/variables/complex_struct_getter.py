"""
Module detecting public state variables with complex struct types
where the automatic getter omits array and mapping members.
"""

from slither.core.declarations import Structure
from slither.core.solidity_types import ArrayType, MappingType, UserDefinedType
from slither.core.solidity_types.type import Type
from slither.core.variables.structure_variable import StructureVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


def _find_omitted_members(
    struct: Structure, seen: set[str] | None = None
) -> list[StructureVariable]:
    """Find struct members that are omitted from the automatic getter.

    Solidity's automatic getters skip array and mapping members in structs.
    This function also recurses into nested structs to find deeply omitted members.
    """
    if seen is None:
        seen = set()

    # Prevent infinite recursion from recursive struct types
    if struct.canonical_name in seen:
        return []
    seen.add(struct.canonical_name)

    omitted: list[StructureVariable] = []
    for member in struct.elems_ordered:
        member_type = member.type
        if isinstance(member_type, (ArrayType, MappingType)):
            omitted.append(member)
        elif isinstance(member_type, UserDefinedType) and isinstance(member_type.type, Structure):
            # Recursively check nested structs
            nested_omitted = _find_omitted_members(member_type.type, seen)
            if nested_omitted:
                omitted.extend(nested_omitted)

    return omitted


class ComplexStructGetter(AbstractDetector):
    """
    Detect public state variables with struct types where the automatic getter
    omits array or mapping members.
    """

    ARGUMENT = "complex-struct-getter"
    HELP = "Public struct getters with omitted members"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#complex-struct-getter"

    WIKI_TITLE = "Complex struct getter"
    WIKI_DESCRIPTION = (
        "Detect public state variables containing structs where the automatic getter "
        "omits array and mapping members. Solidity's generated getters skip these types, "
        "which may cause confusion about data accessibility."
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
struct UserData {
    string name;
    uint256 balance;
    uint256[] tokenIds;
    mapping(address => uint256) allowances;
}

contract Example {
    UserData public userData;
}
```
The automatic getter for `userData` will not return `tokenIds` or `allowances`, \
potentially causing integration issues with external contracts or front-ends."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "Create a custom getter function that returns the omitted members, "
        "or separate complex members into their own state variables."
    )

    def _detect(self) -> list[Output]:
        results = []

        for contract in self.compilation_unit.contracts_derived:
            if contract.is_interface or contract.is_from_dependency():
                continue

            for var in contract.state_variables_declared:
                if var.visibility != "public":
                    continue

                if not isinstance(var.type, UserDefinedType):
                    continue

                if not isinstance(var.type.type, Structure):
                    continue

                struct = var.type.type
                omitted = _find_omitted_members(struct)

                if not omitted:
                    continue

                omitted_names = ", ".join(f"{m.name} ({m.type})" for m in omitted)

                info: DETECTOR_INFO = [
                    var,
                    " is a public state variable of type ",
                    struct,
                    " whose automatic getter omits: ",
                    omitted_names,
                    "\n",
                ]
                res = self.generate_result(info)
                results.append(res)

        return results
