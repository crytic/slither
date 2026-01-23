from slither.core.expressions import Literal
from slither.core.variables.variable import Variable
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.core.solidity_types import ElementaryType

literal_replacements = []


class LIR(AbstractMutator):
    NAME = "LIR"
    HELP = "Literal Integer Replacement"

    def _mutate(self) -> dict:
        result: dict = {}
        variable: Variable

        # Create fault for state variables declaration
        for variable in self.contract.state_variables_declared:
            if variable.initialized:
                # Cannot remove the initialization of constant variables
                if variable.is_constant:
                    continue

                if isinstance(variable.expression, Literal):
                    if isinstance(variable.type, ElementaryType):
                        literal_replacements.append(variable.type.min)  # append data type min value
                        literal_replacements.append(variable.type.max)  # append data type max value
                        if str(variable.type).startswith("uint"):
                            literal_replacements.append("1")
                        elif str(variable.type).startswith("int"):
                            literal_replacements.append("-1")
                    # Get the string
                    start = variable.source_mapping.start
                    stop = start + variable.source_mapping.length
                    old_str = variable.source_mapping.content
                    line_no = variable.node_initialization.source_mapping.lines
                    if line_no[0] not in self.dont_mutate_line:
                        for value in literal_replacements:
                            old_value = old_str[old_str.find("=") + 1 :].strip()
                            if old_value != value:
                                new_str = f"{old_str.split('=')[0]}= {value}"
                                create_patch_with_line(
                                    result,
                                    self.in_file,
                                    start,
                                    stop,
                                    old_str,
                                    new_str,
                                    line_no[0],
                                )

        for function in self.contract.functions_and_modifiers_declared:
            if not self.should_mutate_function(function):
                continue
            for variable in function.local_variables:
                if variable.initialized and isinstance(variable.expression, Literal):
                    if isinstance(variable.type, ElementaryType):
                        literal_replacements.append(variable.type.min)
                        literal_replacements.append(variable.type.max)
                        if str(variable.type).startswith("uint"):
                            literal_replacements.append("1")
                        elif str(variable.type).startswith("int"):
                            literal_replacements.append("-1")
                    start = variable.source_mapping.start
                    stop = start + variable.source_mapping.length
                    old_str = variable.source_mapping.content
                    line_no = variable.source_mapping.lines
                    if line_no[0] not in self.dont_mutate_line:
                        for new_value in literal_replacements:
                            old_value = old_str[old_str.find("=") + 1 :].strip()
                            if old_value != new_value:
                                new_str = f"{old_str.split('=')[0]}= {new_value}"
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
