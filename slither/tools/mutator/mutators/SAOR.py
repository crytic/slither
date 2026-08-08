from slither.core.declarations.function import Function
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.expression import Expression
from slither.slithir.operations import HighLevelCall, InternalCall, LibraryCall
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator
from slither.tools.mutator.utils.patch import create_patch_with_line


def _find_call_expressions(expression: Expression) -> list:
    """Find all CallExpression nodes in an expression tree."""
    from slither.core.expressions.assignment_operation import AssignmentOperation
    from slither.core.expressions.binary_operation import BinaryOperation
    from slither.core.expressions.type_conversion import TypeConversion
    from slither.core.expressions.unary_operation import UnaryOperation
    from slither.core.expressions.member_access import MemberAccess
    from slither.core.expressions.index_access import IndexAccess
    from slither.core.expressions.tuple_expression import TupleExpression

    results = []
    if expression is None:
        return results

    if isinstance(expression, CallExpression):
        results.append(expression)
        for arg in expression.arguments:
            results.extend(_find_call_expressions(arg))
        if expression.called:
            results.extend(_find_call_expressions(expression.called))
    elif isinstance(expression, AssignmentOperation):
        for e in expression.expressions:
            results.extend(_find_call_expressions(e))
    elif isinstance(expression, BinaryOperation):
        results.extend(_find_call_expressions(expression.expression_left))
        results.extend(_find_call_expressions(expression.expression_right))
    elif isinstance(expression, TypeConversion):
        results.extend(_find_call_expressions(expression.expression))
    elif isinstance(expression, UnaryOperation):
        results.extend(_find_call_expressions(expression.expression))
    elif isinstance(expression, MemberAccess):
        results.extend(_find_call_expressions(expression.expression))
    elif isinstance(expression, IndexAccess):
        results.extend(_find_call_expressions(expression.expression_left))
        if expression.expression_right:
            results.extend(_find_call_expressions(expression.expression_right))
    elif isinstance(expression, TupleExpression):
        for e in expression.expressions:
            if e:
                results.extend(_find_call_expressions(e))

    return results


class SAOR(AbstractMutator):
    NAME = "SAOR"
    HELP = "Swap Arguments Order Replacement"

    def _mutate(self) -> dict:
        result: dict = {}

        for function in self.contract.functions_and_modifiers_declared:
            if not self.should_mutate_function(function):
                continue

            for node in function.nodes:
                if not self.should_mutate_node(node):
                    continue

                for ir in node.irs:
                    if not isinstance(ir, (HighLevelCall, InternalCall, LibraryCall)):
                        continue

                    called_func = ir.function
                    if called_func is None or not isinstance(called_func, Function):
                        continue

                    params = called_func.parameters
                    if len(params) < 2 or len(ir.arguments) != len(params):
                        continue

                    # Find a matching CallExpression with the same argument count
                    if not node.expression:
                        continue

                    call_exprs = _find_call_expressions(node.expression)
                    matching_call = next(
                        (c for c in call_exprs if len(c.arguments) == len(params)),
                        None,
                    )
                    if matching_call is None:
                        continue

                    # Find pairs of same-typed parameters
                    for i in range(len(params)):
                        for j in range(i + 1, len(params)):
                            if str(params[i].type) != str(params[j].type):
                                continue

                            arg_i = matching_call.arguments[i]
                            arg_j = matching_call.arguments[j]

                            if not arg_i.source_mapping or not arg_j.source_mapping:
                                continue

                            arg_i_content = arg_i.source_mapping.content
                            arg_j_content = arg_j.source_mapping.content

                            if not arg_i_content or not arg_j_content:
                                continue

                            # Skip if arguments are identical (swap would be a no-op)
                            if arg_i_content == arg_j_content:
                                continue

                            # Build the swapped source by replacing within the node
                            node_start = node.source_mapping.start
                            node_stop = node_start + node.source_mapping.length
                            old_str = node.source_mapping.content
                            line_no = node.source_mapping.lines

                            # Calculate relative offsets within the node
                            i_start = arg_i.source_mapping.start - node_start
                            i_end = i_start + arg_i.source_mapping.length
                            j_start = arg_j.source_mapping.start - node_start
                            j_end = j_start + arg_j.source_mapping.length

                            # Validate offsets are within bounds
                            if (
                                i_start < 0
                                or j_start < 0
                                or i_end > len(old_str)
                                or j_end > len(old_str)
                            ):
                                continue

                            # Swap: replace the later one first to preserve offsets
                            new_str = (
                                old_str[:i_start]
                                + arg_j_content
                                + old_str[i_end:j_start]
                                + arg_i_content
                                + old_str[j_end:]
                            )

                            create_patch_with_line(
                                result,
                                self.in_file,
                                node_start,
                                node_stop,
                                old_str,
                                new_str,
                                line_no[0],
                            )

        return result
