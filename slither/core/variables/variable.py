"""
    Variable module
"""
from typing import Optional, TYPE_CHECKING

from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.solidity_types.type import Type
from slither.core.solidity_types.elementary_type import ElementaryType

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression


class Variable(SourceMapping):
    def __init__(self):
        super(Variable, self).__init__()
        self._name: Optional[str] = None
        self._initial_expression: Optional["Expression"] = None
        self._type: Optional[Type] = None
        self._initialized: Optional[bool] = None
        self._visibility: Optional[str] = None
        self._is_constant = False

    @property
    def is_scalar(self) -> bool:
        return isinstance(self.type, ElementaryType)

    @property
    def expression(self) -> Optional["Expression"]:
        """
            Expression: Expression of the node (if initialized)
            Initial expression may be different than the expression of the node
            where the variable is declared, if its used ternary operator
            Ex: uint a = b?1:2
            The expression associated to a is uint a = b?1:2
            But two nodes are created,
            one where uint a = 1,
            and one where uint a = 2

        """
        return self._initial_expression

    @property
    def initialized(self) -> Optional[bool]:
        """
            boolean: True if the variable is initialized at construction
        """
        return self._initialized

    @property
    def uninitialized(self) -> bool:
        """
            boolean: True if the variable is not initialized
        """
        return not self._initialized

    @property
    def name(self) -> str:
        """
            str: variable name
        """
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def type(self) -> Optional[Type]:
        return self._type

    @property
    def is_constant(self) -> bool:
        return self._is_constant

    @property
    def visibility(self) -> Optional[str]:
        """
            str: variable visibility
        """
        return self._visibility

    def set_type(self, t):
        if isinstance(t, str):
            t = ElementaryType(t)
        assert isinstance(t, (Type, list)) or t is None
        self._type = t

    @property
    def function_name(self):
        """
        Return the name of the variable as a function signature
        :return:
        """
        from slither.core.solidity_types import ArrayType, MappingType
        from slither.utils.type import export_nested_types_from_variable

        variable_getter_args = ""
        return_type = self.type
        assert return_type

        if isinstance(return_type, (ArrayType, MappingType)):
            variable_getter_args = ",".join(map(str, export_nested_types_from_variable(self)))

        return f"{self.name}({variable_getter_args})"

    def __str__(self):
        return self._name
