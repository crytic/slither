import re
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator


function_header_replacements = [
    "pure ==> view",
    "view ==> pure",
    "(\\s)(external|public|internal) ==> \\1private",
    "(\\s)(external|public) ==> \\1internal",
]


class FHR(AbstractMutator):
    NAME = "FHR"
    HELP = "Function Header Replacement"

    def _mutate(self) -> dict:
        result: dict = {}

        for function in self.contract.functions_and_modifiers_declared:
            if not self.should_mutate_function(function):
                continue
            start = function.source_mapping.start
            stop = start + function.source_mapping.content.find("{")
            old_str = function.source_mapping.content
            line_no = function.source_mapping.lines
            if line_no[0] not in self.dont_mutate_line:
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
