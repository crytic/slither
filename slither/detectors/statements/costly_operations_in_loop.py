from slither.core.cfg.node import NodeType
from slither.core.solidity_types.array_type import ArrayType
from slither.core.solidity_types.mapping_type import MappingType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class CostlyOperationsInLoop(AbstractDetector):

    ARGUMENT = "costly-loop"
    HELP = "Costly operations in a loop"
    IMPACT = DetectorClassification.INFORMATIONAL
    # Overall the detector seems precise, but it does not take into account
    # case where there are external calls or internal calls that might read the state
    # variable changes. In these cases the optimization should not be applied
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#costly-operations-inside-a-loop"

    WIKI_TITLE = "Costly operations inside a loop"
    WIKI_DESCRIPTION = (
        "Costly operations inside a loop might waste gas, so optimizations are justified."
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract CostlyOperationsInLoop{

    uint loop_count = 100;
    uint state_variable=0;

    function bad() external{
        for (uint i=0; i < loop_count; i++){
            state_variable++;
        }
    }

    function good() external{
      uint local_variable = state_variable;
      for (uint i=0; i < loop_count; i++){
        local_variable++;
      }
      state_variable = local_variable;
    }
}
```
Incrementing `state_variable` in a loop incurs a lot of gas because of expensive `SSTOREs`, which might lead to an `out-of-gas`."""
    # endregion wiki_exploit_scenario
    
    WIKI_RECOMMENDATION = "Use a local variable to hold the loop computation result."

    @staticmethod
    def costly_operations_in_loop(node, in_loop, visited, ret):
        if node in visited:
            return
        # shared visited
        visited.append(node)

        if node.type == NodeType.STARTLOOP:
            in_loop = True
        elif node.type == NodeType.ENDLOOP:
            in_loop = False

        if in_loop:
            sv_written = node.state_variables_written
            for sv in sv_written:
                # Ignore Array/Mapping/Struct types for now
                if isinstance(sv.type, (ArrayType, MappingType)):
                    continue
                ret.append(node)
                break

        for son in node.sons:
            CostlyOperationsInLoop.costly_operations_in_loop(son, in_loop, visited, ret)

    @staticmethod
    def detect_costly_operations_in_loop(contract):
        ret = []
        for f in contract.functions + contract.modifiers:
            if f.contract_declarer == contract and f.is_implemented:
                CostlyOperationsInLoop.costly_operations_in_loop(f.entry_point, False, [], ret)

        return ret

    def _detect(self):
        """"""
        results = []
        for c in self.compilation_unit.contracts_derived:
            values = self.detect_costly_operations_in_loop(c)
            for node in values:
                func = node.function
                info = [func, " has costly operations inside a loop:\n"]
                info += ["\t- ", node, "\n"]
                res = self.generate_result(info)
                results.append(res)

        return results
