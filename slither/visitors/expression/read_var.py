from typing import Any, List, Union, Optional

from slither.core.expressions import NewElementaryType
from slither.visitors.expression.expression import ExpressionVisitor

from slither.core.expressions.assignment_operation import (
    AssignmentOperation,
    AssignmentOperationType,
)

from slither.core.variables.variable import Variable
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.expressions.binary_operation import BinaryOperation
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.conditional_expression import ConditionalExpression
from slither.core.expressions.elementary_type_name_expression import ElementaryTypeNameExpression
from slither.core.expressions.expression import Expression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.index_access import IndexAccess
from slither.core.expressions.literal import Literal
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.new_array import NewArray
from slither.core.expressions.new_contract import NewContract
from slither.core.expressions.tuple_expression import TupleExpression
from slither.core.expressions.type_conversion import TypeConversion
from slither.core.expressions.unary_operation import UnaryOperation


key = "ReadVar"


def get(expression: Expression) -> List[Union[Identifier, IndexAccess, Any]]:
    val = expression.context[key]
    # we delete the item to reduce memory use
    del expression.context[key]
    return val


def set_val(expression: Expression, val: List[Union[Identifier, IndexAccess, Any]]) -> None:
    expression.context[key] = val


class ReadVar(ExpressionVisitor):
    def __init__(self, expression: Expression) -> None:
        self._result: Optional[List[Expression]] = None
        super().__init__(expression)

    def result(self) -> List[Expression]:
        if self._result is None:
            self._result = list(set(get(self.expression)))
        return self._result

    # overide assignement
    # dont explore if its direct assignement (we explore if its +=, -=, ...)
    def _visit_assignement_operation(self, expression: AssignmentOperation) -> None:
        if expression.type != AssignmentOperationType.ASSIGN:
            self._visit_expression(expression.expression_left)
        self._visit_expression(expression.expression_right)

    def _post_assignement_operation(self, expression: AssignmentOperation) -> None:
        if expression.type != AssignmentOperationType.ASSIGN:
            left = get(expression.expression_left)
        else:
            left = []
        right = get(expression.expression_right)
        val = left + right
        set_val(expression, val)

    def _post_binary_operation(self, expression: BinaryOperation) -> None:
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = left + right
        set_val(expression, val)

    def _post_call_expression(self, expression: CallExpression) -> None:
        called = get(expression.called)
        argss = [get(a) for a in expression.arguments if a]
        args = [item for sublist in argss for item in sublist]
        val = called + args
        set_val(expression, val)

    def _post_conditional_expression(self, expression: ConditionalExpression) -> None:
        if_expr = get(expression.if_expression)
        else_expr = get(expression.else_expression)
        then_expr = get(expression.then_expression)
        val = if_expr + else_expr + then_expr
        set_val(expression, val)

    def _post_elementary_type_name_expression(
        self, expression: ElementaryTypeNameExpression
    ) -> None:
        set_val(expression, [])

    # save only identifier expression
    def _post_identifier(self, expression: Identifier) -> None:
        if isinstance(expression.value, Variable):
            set_val(expression, [expression])
        elif isinstance(expression.value, SolidityVariable):
            # TODO: investigate if this branch can be reached, and if Identifier.value has the correct type
            set_val(expression, [expression])
        else:
            set_val(expression, [])

    def _post_index_access(self, expression: IndexAccess) -> None:
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = left + right + [expression]
        set_val(expression, val)

    def _post_literal(self, expression: Literal) -> None:
        set_val(expression, [])

    def _post_member_access(self, expression: MemberAccess) -> None:
        expr = get(expression.expression)
        val = expr
        set_val(expression, val)

    def _post_new_array(self, expression: NewArray) -> None:
        set_val(expression, [])

    def _post_new_contract(self, expression: NewContract) -> None:
        set_val(expression, [])

    def _post_new_elementary_type(self, expression: NewElementaryType) -> None:
        set_val(expression, [])

    def _post_tuple_expression(self, expression: TupleExpression) -> None:
        expressions = [get(e) for e in expression.expressions if e]
        val = [item for sublist in expressions for item in sublist]
        set_val(expression, val)

    def _post_type_conversion(self, expression: TypeConversion) -> None:
        expr = get(expression.expression)
        val = expr
        set_val(expression, val)

    def _post_unary_operation(self, expression: UnaryOperation) -> None:
        expr = get(expression.expression)
        val = expr
        set_val(expression, val)
