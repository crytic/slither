from typing import Union, List

from slither.core.expressions.binary_operation import BinaryOperation
from slither.core.expressions.expression import Expression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.literal import Literal
from slither.core.expressions.tuple_expression import TupleExpression
from slither.core.expressions.type_conversion import TypeConversion
from slither.core.expressions.unary_operation import UnaryOperation


class ConditionalExpression(Expression):
    def __init__(
        self,
        if_expression: Union[BinaryOperation, Identifier, Literal],
        then_expression: Union[
            "ConditionalExpression", TypeConversion, Literal, TupleExpression, Identifier
        ],
        else_expression: Union[TupleExpression, UnaryOperation, Identifier, Literal],
    ) -> None:
        assert isinstance(if_expression, Expression)
        assert isinstance(then_expression, Expression)
        assert isinstance(else_expression, Expression)
        super().__init__()
        self._if_expression: Expression = if_expression
        self._then_expression: Expression = then_expression
        self._else_expression: Expression = else_expression

    @property
    def expressions(self) -> List[Expression]:
        return [self._if_expression, self._then_expression, self._else_expression]

    @property
    def if_expression(self) -> Expression:
        return self._if_expression

    @property
    def else_expression(self) -> Expression:
        return self._else_expression

    @property
    def then_expression(self) -> Expression:
        return self._then_expression

    def __str__(self) -> str:
        return (
            "if "
            + str(self._if_expression)
            + " then "
            + str(self._then_expression)
            + " else "
            + str(self._else_expression)
        )
