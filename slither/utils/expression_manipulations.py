"""
    We use protected member, to avoid having setter in the expression
    as they should be immutable
"""
import copy
from typing import Union, Callable
from slither.core.expressions import UnaryOperation
from slither.core.expressions.assignment_operation import AssignmentOperation
from slither.core.expressions.binary_operation import BinaryOperation
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.conditional_expression import ConditionalExpression
from slither.core.expressions.expression import Expression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.index_access import IndexAccess
from slither.core.expressions.literal import Literal
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.new_array import NewArray
from slither.core.expressions.new_contract import NewContract
from slither.core.expressions.tuple_expression import TupleExpression
from slither.core.expressions.type_conversion import TypeConversion
from slither.all_exceptions import SlitherException

# pylint: disable=protected-access
def f_expressions(
    e: AssignmentOperation, x: Union[Identifier, Literal, MemberAccess, IndexAccess]
) -> None:
    e._expressions.append(x)


def f_call(e, x):
    e._arguments.append(x)


def f_expression(e, x):
    e._expression = x


def f_called(e, x):
    e._called = x


class SplitTernaryExpression:
    def __init__(self, expression: Union[AssignmentOperation, ConditionalExpression]) -> None:

        if isinstance(expression, ConditionalExpression):
            self.true_expression = copy.copy(expression.then_expression)
            self.false_expression = copy.copy(expression.else_expression)
            self.condition = copy.copy(expression.if_expression)
        else:
            self.true_expression = copy.copy(expression)
            self.false_expression = copy.copy(expression)
            self.condition = None
            self.copy_expression(expression, self.true_expression, self.false_expression)

    def apply_copy(
        self,
        next_expr: Expression,
        true_expression: Union[AssignmentOperation, MemberAccess],
        false_expression: Union[AssignmentOperation, MemberAccess],
        f: Callable,
    ) -> bool:

        if isinstance(next_expr, ConditionalExpression):
            f(true_expression, copy.copy(next_expr.then_expression))
            f(false_expression, copy.copy(next_expr.else_expression))
            self.condition = copy.copy(next_expr.if_expression)
            return False

        f(true_expression, copy.copy(next_expr))
        f(false_expression, copy.copy(next_expr))
        return True

    # pylint: disable=too-many-branches
    def copy_expression(
        self, expression: Expression, true_expression: Expression, false_expression: Expression
    ) -> None:
        if self.condition:
            return

        if isinstance(expression, ConditionalExpression):
            raise SlitherException("Nested ternary operator not handled")

        if isinstance(expression, (Literal, Identifier, IndexAccess, NewArray, NewContract)):
            return

        # case of lib
        # (.. ? .. : ..).add
        if isinstance(expression, MemberAccess):
            next_expr = expression.expression
            if self.apply_copy(next_expr, true_expression, false_expression, f_expression):
                self.copy_expression(
                    next_expr, true_expression.expression, false_expression.expression
                )

        elif isinstance(expression, (AssignmentOperation, BinaryOperation, TupleExpression)):
            true_expression._expressions = []
            false_expression._expressions = []

            for next_expr in expression.expressions:
                if isinstance(next_expr, IndexAccess):
                    # create an index access for each branch
                    if isinstance(next_expr.expression_right, ConditionalExpression):
                        next_expr = _handle_ternary_access(
                            next_expr, true_expression, false_expression
                        )
                if self.apply_copy(next_expr, true_expression, false_expression, f_expressions):
                    # always on last arguments added
                    self.copy_expression(
                        next_expr,
                        true_expression.expressions[-1],
                        false_expression.expressions[-1],
                    )

        elif isinstance(expression, CallExpression):
            next_expr = expression.called

            # case of lib
            # (.. ? .. : ..).add
            if self.apply_copy(next_expr, true_expression, false_expression, f_called):
                self.copy_expression(next_expr, true_expression.called, false_expression.called)

            true_expression._arguments = []
            false_expression._arguments = []

            for next_expr in expression.arguments:
                if self.apply_copy(next_expr, true_expression, false_expression, f_call):
                    # always on last arguments added
                    self.copy_expression(
                        next_expr,
                        true_expression.arguments[-1],
                        false_expression.arguments[-1],
                    )

        elif isinstance(expression, (TypeConversion, UnaryOperation)):
            next_expr = expression.expression
            if self.apply_copy(next_expr, true_expression, false_expression, f_expression):
                self.copy_expression(
                    expression.expression,
                    true_expression.expression,
                    false_expression.expression,
                )

        else:
            raise SlitherException(
                f"Ternary operation not handled {expression}({type(expression)})"
            )


def _handle_ternary_access(
    next_expr: IndexAccess,
    true_expression: AssignmentOperation,
    false_expression: AssignmentOperation,
):
    """
    Conditional ternary accesses are split into two accesses, one true and one false
    E.g.  x[if cond ? 1 : 2] -> if cond { x[1] } else { x[2] }
    """
    true_index_access = IndexAccess(
        next_expr.expression_left,
        next_expr.expression_right.then_expression,
        next_expr.type,
    )
    false_index_access = IndexAccess(
        next_expr.expression_left,
        next_expr.expression_right.else_expression,
        next_expr.type,
    )

    f_expressions(
        true_expression,
        true_index_access,
    )
    f_expressions(
        false_expression,
        false_index_access,
    )

    return next_expr.expression_right
