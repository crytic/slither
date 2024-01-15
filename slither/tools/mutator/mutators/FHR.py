from typing import Dict
from slither.formatters.utils.patches import create_patch
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator, FaultNature
import re

# INFO: low severity

function_header_replacements = [
    "pure ==> view",
    "view ==> pure",
    "(\s)(external|public|internal) ==> \\1private",
    "(\s)(external|public) ==> \\1internal"
]

class FHR(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "FHR"
    HELP = 'Function Header Replacement'
    FAULTNATURE = FaultNature.Missing

    def _mutate(self) -> Dict:
        result: Dict = {}
        
        for function in self.contract.functions_and_modifiers_declared: 
            # function_header = function.source_mapping.content.split('{')[0]
            start = function.source_mapping.start
            stop = start + function.source_mapping.content.find('{')
            old_str = self.in_file_str[start:stop]
            line_no = function.source_mapping.lines
            for value in function_header_replacements:
                left_value = value.split(" ==> ")[0]
                right_value = value.split(" ==> ")[1]
                if re.search(re.compile(left_value), old_str) != None:
                    new_str = re.sub(re.compile(left_value), right_value, old_str)
                    create_patch(result, self.in_file, start, stop, old_str, new_str, line_no[0])
                                         
        return result    