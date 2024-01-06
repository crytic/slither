from typing import Dict
from slither.core.cfg.node import NodeType
from slither.formatters.utils.patches import create_patch
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator, FaultNature, FaultClass

class MIA(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "MIA"
    HELP = '"if" construct around statement'
    FAULTCLASS = FaultClass.Checking
    FAULTNATURE = FaultNature.Missing

    def _mutate(self) -> Dict:

        result: Dict = {}
        # Retrieve the file
        in_file = self.contract.source_mapping.filename.absolute
        # Retrieve the source code
        in_file_str = self.contract.compilation_unit.core.source_code[in_file]
        
        for function in self.contract.functions_declared + list(self.contract.modifiers_declared):
            for node in function.nodes:
                if node.type == NodeType.IF:
                    
                    # Get the string
                    start = node.source_mapping.start
                    stop = start + node.source_mapping.length
                    old_str = in_file_str[start:stop]
                    line_no = node.source_mapping.lines

                    # Replace the expression with true and false
                    for value in ["true", "false"]:
                        new_str = value
                        create_patch(result, in_file, start, stop, old_str, new_str, line_no[0])
                                         
        return result

    

    
        
    