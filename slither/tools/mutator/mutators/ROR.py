from slither.core.expressions import BinaryOperation
from slither.slithir.operations import Binary, BinaryType
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator

relational_operators = [
    BinaryType.LESS,
    BinaryType.GREATER,
    BinaryType.LESS_EQUAL,
    BinaryType.GREATER_EQUAL,
    BinaryType.EQUAL,
    BinaryType.NOT_EQUAL,
]


class ROR(AbstractMutator):
    NAME = "ROR"
    HELP = "Relational Operator Replacement"

    def _mutate(self) -> dict:
        result: dict = {}

        for function in self.contract.functions_and_modifiers_declared:
            if not self.should_mutate_function(function):
                continue
            for node in function.nodes:
                if not self.should_mutate_node(node):
                    continue
                for ir in node.irs:
                    if isinstance(ir, Binary) and ir.type in relational_operators:
                        if (
                            str(ir.variable_left.type) != "address"
                            and str(ir.variable_right) != "address"
                        ):
                            expression = ir.expression
                            if not isinstance(expression, BinaryOperation):
                                continue
                            start = expression.source_mapping.start
                            stop = start + expression.source_mapping.length
                            old_str = expression.source_mapping.content
                            line_no = node.source_mapping.lines
                            # Replace the operator between the operands, not one inside them.
                            left = expression.expression_left.source_mapping
                            left_end = left.start + left.length - start
                            right_start = expression.expression_right.source_mapping.start - start
                            gap = old_str[left_end:right_start]
                            alternative_ops = relational_operators[:]
                            alternative_ops.remove(ir.type)
                            for op in alternative_ops:
                                new_gap = gap.replace(ir.type.value, op.value, 1)
                                new_str = f"{old_str[:left_end]}{new_gap}{old_str[right_start:]}"
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
