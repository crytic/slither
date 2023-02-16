from typing import TYPE_CHECKING, Union, Optional

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression
    from slither.slithir.operations import Operation


class ChildExpression:
    def __init__(self) -> None:
        super().__init__()
        # TODO remove all the setters for the child objects
        # And make it a constructor arguement
        # This will remove the optional
        self._expression: Optional[Union["Expression", "Operation"]] = None

    def set_expression(self, expression: Union["Expression", "Operation"]) -> None:
        # TODO investigate when this can be an operation?
        # It was auto generated during an AST or detectors tests
        self._expression = expression

    @property
    def expression(self) -> Union["Expression", "Operation"]:
        return self._expression  # type: ignore
