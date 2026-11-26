from slither.core.expressions.expression import Expression


class IndexRangeAccess(Expression):
    """
    Array slice: base[start:end]
    Both start and end are optional (e.g. data[4:], data[:4], data[:]).
    """

    def __init__(
        self,
        base_expression: Expression,
        start_expression: Expression | None,
        end_expression: Expression | None,
    ) -> None:
        super().__init__()
        # start/end can be None; SplitTernaryExpression relies on _expressions
        self._expressions: list[Expression | None] = [
            base_expression,
            start_expression,
            end_expression,
        ]

    @property
    def expressions(self) -> list[Expression | None]:
        return self._expressions

    @property
    def expression_base(self) -> Expression:
        return self._expressions[0]  # type: ignore

    @property
    def expression_start(self) -> Expression | None:
        return self._expressions[1]

    @property
    def expression_end(self) -> Expression | None:
        return self._expressions[2]

    def __str__(self) -> str:
        start = str(self.expression_start) if self.expression_start is not None else ""
        end = str(self.expression_end) if self.expression_end is not None else ""
        return f"{self.expression_base}[{start}:{end}]"
