from typing import Dict
from slither.core.expressions import Literal
from slither.core.variables.variable import Variable
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator
from slither.tools.mutator.utils.patch import create_patch_with_line


class MVIV(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "MVIV"
    HELP = "variable initialization using a value"

    def _mutate(self) -> Dict:
        result: Dict = {}
        variable: Variable

        # Create fault for state variables declaration
        for variable in self.contract.state_variables_declared:
            if variable.initialized:
                # Cannot remove the initialization of constant variables
                if variable.is_constant:
                    continue

                if isinstance(variable.expression, Literal):
                    # Get the string
                    start = variable.source_mapping.start
                    stop = variable.expression.source_mapping.start
                    old_str = self.in_file_str[start:stop]
                    new_str = old_str[: old_str.find("=")]
                    line_no = variable.node_initialization.source_mapping.lines
                    if not line_no[0] in self.dont_mutate_line:
                        create_patch_with_line(
                            result,
                            self.in_file,
                            start,
                            stop + variable.expression.source_mapping.length,
                            old_str,
                            new_str,
                            line_no[0],
                        )

        for function in self.contract.functions_and_modifiers_declared:
            for variable in function.local_variables:
                if variable.initialized and isinstance(variable.expression, Literal):
                    start = variable.source_mapping.start
                    stop = variable.expression.source_mapping.start
                    old_str = self.in_file_str[start:stop]
                    new_str = old_str[: old_str.find("=")]
                    line_no = variable.source_mapping.lines
                    if not line_no[0] in self.dont_mutate_line:
                        create_patch_with_line(
                            result,
                            self.in_file,
                            start,
                            stop + variable.expression.source_mapping.length,
                            old_str,
                            new_str,
                            line_no[0],
                        )
        return result
