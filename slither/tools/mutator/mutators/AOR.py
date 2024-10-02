from typing import Dict
from slither.slithir.operations import Binary, BinaryType
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator
from slither.core.variables.variable import Variable
from slither.core.expressions.unary_operation import UnaryOperation
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.identifier import Identifier
from slither.core.solidity_types.array_type import ArrayType

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
                    and isinstance(ir_expression.called.expression, Identifier)
                    and isinstance(ir_expression.called.expression.value, Variable)
                    and isinstance(ir_expression.called.expression.value.type, ArrayType)
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
                    and isinstance(ir_expression.called.expression, Identifier)
                    and isinstance(ir_expression.called.expression.value, Variable)
                    and isinstance(ir_expression.called.expression.value.type, ArrayType)
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
                            old_str = self.in_file_str[start:stop]
                            line_no = node.source_mapping.lines
                            if not line_no[0] in self.dont_mutate_line:
                                # Replace the expression with true
                                new_str = f"{old_str.split(ir.type.value)[0]}{op.value}{old_str.split(ir.type.value)[1]}"
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
