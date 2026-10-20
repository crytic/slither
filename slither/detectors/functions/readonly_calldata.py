from packaging.version import Version

from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.declarations import Function
from slither.core.variables import LocalVariable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.detectors.functions.external_function import ExternalFunction
from slither.slithir.operations import (
    Call,
    Index,
    Length,
    Member,
    OperationWithLValue,
    SolidityCall,
)
from slither.slithir.variables import ReferenceVariable
from slither.utils.output import Output


def readonly_parameters(function: Function) -> list[LocalVariable]:
    if (
        function.visibility != "external"
        or not function.is_implemented
        or function.contains_assembly
        or function.modifiers
        or any(
            ExternalFunction.is_reference_type(v)
            for v in function.local_variables + function.returns
        )
        or any(
            ExternalFunction.is_reference_type(v) and v in function.variables_written
            for v in function.parameters
        )
    ):
        return []
    operations = [ir for node in function.nodes for ir in node.irs]
    if any(isinstance(ir, Call) and not isinstance(ir, SolidityCall) for ir in operations):
        return []
    candidates = []
    for parameter in function.parameters:
        if parameter.location != "memory" or not ExternalFunction.is_reference_type(parameter):
            continue
        if parameter in function.variables_written or parameter not in function.variables_read:
            continue
        writes = [
            ir.lvalue
            for ir in operations
            if isinstance(ir, OperationWithLValue) and not isinstance(ir, (Index, Member, Length))
        ]
        if any(
            isinstance(v, ReferenceVariable)
            and (
                v.points_to_origin is parameter
                or is_dependent(v.points_to_origin, parameter, function)
            )
            for v in writes
        ):
            continue
        candidates.append(parameter)
    return candidates


class GasReadonlyCalldata(AbstractDetector):
    ARGUMENT = "readonly-calldata"
    HELP = "Read-only external memory parameters that could use calldata"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM
    LANGUAGE = "solidity"
    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#read-only-calldata"
    WIKI_TITLE = "Read-only calldata"
    WIKI_DESCRIPTION = (
        "Finds used, unmodified external memory arrays, structs, bytes and strings on Solidity "
        ">=0.6.9. Conservatively excludes assembly, modifiers, non-builtin calls, parameter "
        "reassignment and local/return reference aliases. Cast-derived writes use data dependency analysis. Complements the legacy external-function check."
    )
    WIKI_EXPLOIT_SCENARIO = """
```solidity
function first(uint256[] memory data) external pure returns (uint256) {
    return data[0]; // the parameter could be calldata
}
```
"""
    WIKI_RECOMMENDATION = (
        "Consider calldata for the reported parameter to avoid an entry-time memory copy. "
        "Compile and benchmark with the project's exact compiler and optimizer settings."
    )

    def _detect(self) -> list[Output]:
        if Version(self.compilation_unit.solc_version) < Version("0.6.9"):
            return []
        return [
            self.generate_result(
                [function, " could use calldata for read-only memory parameter ", parameter, ".\n"]
            )
            for function in sorted(self.compilation_unit.functions, key=lambda f: f.canonical_name)
            for parameter in readonly_parameters(function)
        ]
