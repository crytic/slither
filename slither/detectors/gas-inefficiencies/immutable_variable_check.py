from collections import defaultdict

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import VariableIncrements
from slither.analyses.data_dependency.data_dependency import is_tainted
from slither.core.solidity_types.elementary_type import ElementaryType


class GasImmutableVariableCheck(AbstractDetector):
    """
    Gas: Setting state variables as immutable where possible will save gas.
    """

    ARGUMENT = "immutable-variable-check"
    HELP = "A state variable that will remain constant can be set as immutable to save gas."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#change-state-variables-to-immutable-where-possible"
    WIKI_TITLE = "Change state variables to immutable where possible"
    WIKI_DESCRIPTION = "Setting contract-level state variables to immutable at construction time will store the variable in code rather than storage. Any subsequent reads will be done by the push32 value instruction, rather than sload, making it much more gas-efficient." 

    def analyze(self):
        variable_reads = defaultdict(int)
        variable_writes = defaultdict(int)
        for function in self.contract.functions:
            for node in function.nodes:
                for ir in node.irs:
                    if isinstance(ir, VariableIncrements):
                        variable = ir.variable
                        if isinstance(variable.type, ElementaryType) and variable.visibility == "public":
                            if is_tainted(ir.operand, {"tainted": [variable]}, {"tainted": []}):
                                variable_reads[variable.name] += 1
                            else:
                                variable_writes[variable.name] += 1
        for variable_name, read_count in variable_reads.items():
            if read_count > 0 and variable_writes[variable_name] == 0:
                variable = self.contract.variable(variable_name)
                if variable and not variable.immutable:
                    self._issues.append({"variable": variable_name, "lineno": variable.lineno})
"run slither <path-to-contract> GasImmutableVariableCheck"