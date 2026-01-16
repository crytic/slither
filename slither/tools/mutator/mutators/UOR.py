from slither.core.expressions.unary_operation import UnaryOperationType, UnaryOperation
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator

unary_operators = [
    UnaryOperationType.PLUSPLUS_PRE,
    UnaryOperationType.MINUSMINUS_PRE,
    UnaryOperationType.PLUSPLUS_POST,
    UnaryOperationType.MINUSMINUS_POST,
    UnaryOperationType.MINUS_PRE,
]


class UOR(AbstractMutator):
    NAME = "UOR"
    HELP = "Unary Operator Replacement"

    def _mutate(self) -> dict:
        result: dict = {}

        for function in self.contract.functions_and_modifiers_declared:
            if not self.should_mutate_function(function):
                continue
            for node in function.nodes:
                if not self.should_mutate_node(node):
                    continue
                try:
                    ir_expression = node.expression
                except AttributeError:
                    continue
                start = node.source_mapping.start
                stop = start + node.source_mapping.length
                old_str = node.source_mapping.content
                line_no = node.source_mapping.lines
                if (
                    isinstance(ir_expression, UnaryOperation)
                    and ir_expression.type in unary_operators
                ):
                    for op in unary_operators:
                        if not node.expression.is_prefix:
                            if node.expression.type != op:
                                variable_read = node.variables_read[0]
                                new_str = str(variable_read) + str(op)
                                if new_str != old_str and str(op) != "-":
                                    create_patch_with_line(
                                        result,
                                        self.in_file,
                                        start,
                                        stop,
                                        old_str,
                                        new_str,
                                        line_no[0],
                                    )
                                new_str = str(op) + str(variable_read)
                                create_patch_with_line(
                                    result,
                                    self.in_file,
                                    start,
                                    stop,
                                    old_str,
                                    new_str,
                                    line_no[0],
                                )
                        else:
                            if node.expression.type != op:
                                variable_read = node.variables_read[0]
                                new_str = str(op) + str(variable_read)
                                if new_str != old_str and str(op) != "-":
                                    create_patch_with_line(
                                        result,
                                        self.in_file,
                                        start,
                                        stop,
                                        old_str,
                                        new_str,
                                        line_no[0],
                                    )
                                new_str = str(variable_read) + str(op)
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
