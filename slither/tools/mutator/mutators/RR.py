from typing import Dict
from slither.core.cfg.node import NodeType
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator, FaultNature


class RR(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "RR"
    HELP = 'Revert Replacement'
    FAULTNATURE = FaultNature.Missing

    def _mutate(self) -> Dict:
        result: Dict = {}

        for function in self.contract.functions_and_modifiers_declared:
            for node in function.nodes:
                if node.type != NodeType.ENTRYPOINT and NodeType.ENDIF != node.type and NodeType.ENDLOOP != node.type:
                    # Get the string
                    start = node.source_mapping.start
                    stop = start + node.source_mapping.length
                    old_str = self.in_file_str[start:stop] 
                    line_no = node.source_mapping.lines
                    if not line_no[0] in self.dont_mutate_line:
                        if old_str != 'revert()':
                            new_str = 'revert()'
                            create_patch_with_line(result, self.in_file, start, stop, old_str, new_str, line_no[0])
        return result

    

    
        
    