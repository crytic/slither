from typing import Dict
from slither.slithir.operations import Binary, BinaryType
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator
from slither.core.expressions.unary_operation import UnaryOperation
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.member_access import MemberAccess

arithmetic_operators = [
    BinaryType.ADDITION,
    BinaryType.DIVISION,
    BinaryType.MULTIPLICATION,
    BinaryType.SUBTRACTION,
    BinaryType.MODULO,
]


class AOR(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "AOR"
    HELP = "Arithmetic operator replacement"

    def _mutate(self) -> Dict:
        result: Dict = {}
        for (  # pylint: disable=too-many-nested-blocks
            function
        ) in self.contract.functions_and_modifiers_declared:
            for node in function.nodes:
                if not self.should_mutate_node(node):
                    continue
                try:
                    ir_expression = node.expression
                except:  # pylint: disable=bare-except
                    continue

                # Special cases handling .push and .pop on dynamic arrays.
                # The IR for these operations has a binary operation due to internal conversion
                # (see convert_to_push and convert_to_pop in slithir/convert.py)
                # however it's not present in the source code and should not be mutated.
                # pylint: disable=too-many-boolean-expressions
                if (
                    isinstance(ir_expression, CallExpression)
                    and isinstance(ir_expression.called, MemberAccess)
                    and ir_expression.called.member_name == "pop"
                ):
                    continue

                # For a .push instruction we skip the last 6 IR operations
                # because they are fixed based on the internal conversion to the IR
                # while we need to look at the preceding instructions because
                # they might contain Binary IR to be mutated.
                # For example for a.push(3+x) it's correct to mutate 3+x.
                irs = (
                    node.irs[:-6]
                    if isinstance(ir_expression, CallExpression)
                    and isinstance(ir_expression.called, MemberAccess)
                    and ir_expression.called.member_name == "push"
                    else node.irs
                )

                for ir in irs:
                    if isinstance(ir, Binary) and ir.type in arithmetic_operators:
                        if isinstance(ir_expression, UnaryOperation):
                            continue
                        alternative_ops = arithmetic_operators[:]
                        alternative_ops.remove(ir.type)
                        for op in alternative_ops:
                            # Get the string
                            start = node.source_mapping.start
                            stop = start + node.source_mapping.length
                            old_str = node.source_mapping.content
                            line_no = node.source_mapping.lines
                            halves = old_str.split(ir.type.value)
                            if len(halves) != 2:
                                continue  # skip if assembly
                            new_str = f"{halves[0]}{op.value}{halves[1]}"
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
