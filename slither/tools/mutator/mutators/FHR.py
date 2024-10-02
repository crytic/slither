from typing import Dict
import re
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator


function_header_replacements = [
    "pure ==> view",
    "view ==> pure",
    "(\\s)(external|public|internal) ==> \\1private",
    "(\\s)(external|public) ==> \\1internal",
]


class FHR(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "FHR"
    HELP = "Function Header Replacement"

    def _mutate(self) -> Dict:
        result: Dict = {}

        for function in self.contract.functions_and_modifiers_declared:
            start = function.source_mapping.start
            stop = start + function.source_mapping.content.find("{")
            old_str = self.in_file_str[start:stop]
            line_no = function.source_mapping.lines
            if not line_no[0] in self.dont_mutate_line:
                for value in function_header_replacements:
                    left_value = value.split(" ==> ", maxsplit=1)[0]
                    right_value = value.split(" ==> ")[1]
                    if re.search(re.compile(left_value), old_str) is not None:
                        new_str = re.sub(re.compile(left_value), right_value, old_str)
                        create_patch_with_line(
                            result,
                            self.in_file,
                            start,
                            stop,
                            old_str,
                            new_str,
                            line_no[0],
                        )
        return result
