"""
Module detecting dangerous conversion to enum
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import TypeConversion
from slither.core.declarations.enum import Enum


def _uses_vulnerable_solc_version(version):
    """Detect if used compiler version is 0.4.[0|1|2|3|4]
    Args:
       version (solc version used)
    Returns:
       Bool
    """
    if version in ["0.4.0", "0.4.1", "0.4.2", "0.4.3", "0.4.4"]:
        return True
    return False


def _detect_dangerous_enum_conversions(contract):
    """Detect dangerous conversion to enum by checking IR
    Args:
         contract (Contract)
    Returns:
         list[(node, variable)] (Nodes where a variable is being converted into enum)
    """
    return [
        (n, ir.variable)
        for f in contract.functions_declared
        for n in f.nodes
        for ir in n.irs
        if isinstance(ir, TypeConversion) and isinstance(ir.type.type, Enum)
    ]


class EnumConversion(AbstractDetector):
    """
    Detect dangerous conversion to enum
    """

    ARGUMENT = "enum-conversion"
    HELP = "Detect dangerous enum conversion"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-enum-conversion"
    WIKI_TITLE = "Dangerous enum conversion"
    WIKI_DESCRIPTION = "Detect out-of-range `enum` conversion (`solc` < `0.4.5`)."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
    pragma solidity 0.4.2;
    contract Test{
    
    enum E{a}
    
    function bug(uint a) public returns(E){
        return E(a);   
    }
}
```
Attackers can trigger unexpected behaviour by calling `bug(1)`."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Use a recent compiler version. If `solc` <`0.4.5` is required, check the `enum` conversion range."

    def _detect(self):
        """Detect dangerous conversion to enum"""
        results = []
        # If solc version >= 0.4.5 then return
        if not _uses_vulnerable_solc_version(self.compilation_unit.solc_version):
            return results

        for c in self.compilation_unit.contracts:
            ret = _detect_dangerous_enum_conversions(c)
            for node, var in ret:
                func_info = [node, " has a dangerous enum conversion\n"]
                # Output each node with the function info header as a separate result.
                variable_info = ["\t- Variable: ", var, f" of type: {str(var.type)}\n"]
                node_info = ["\t- Enum conversion: ", node, "\n"]
                json = self.generate_result(func_info + variable_info + node_info)
                results.append(json)

        return results
