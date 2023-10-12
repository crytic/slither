"""
    Variable module
"""
from typing import Optional, TYPE_CHECKING, List, Union, Tuple

from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.solidity_types.type import Type
from slither.core.solidity_types.elementary_type import ElementaryType

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression

# pylint: disable=too-many-instance-attributes
class Variable(SourceMapping):
    def __init__(self) -> None:
        super().__init__()
        self._name: Optional[str] = None
        self._initial_expression: Optional["Expression"] = None
        self._type: Optional[Type] = None
        self._initialized: Optional[bool] = None
        self._visibility: Optional[str] = None
        self._is_constant = False
        self._is_immutable: bool = False
        self._is_reentrant: bool = True
        self._write_protection: Optional[List[str]] = None

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

    @expression.setter
    def expression(self, expr: "Expression") -> None:
        self._initial_expression = expr

    @property
    def initialized(self) -> Optional[bool]:
        """
        boolean: True if the variable is initialized at construction
        """
        return self._initialized

    @initialized.setter
    def initialized(self, is_init: bool) -> None:
        self._initialized = is_init

    @property
    def uninitialized(self) -> bool:
        """
        boolean: True if the variable is not initialized
        """
        return not self._initialized

    @property
    def name(self) -> Optional[str]:
        """
        str: variable name
        """
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def type(self) -> Optional[Type]:
        return self._type

    @type.setter
    def type(self, new_type: Type) -> None:
        assert isinstance(new_type, Type)
        self._type = new_type

    @property
    def is_constant(self) -> bool:
        return self._is_constant

    @is_constant.setter
    def is_constant(self, is_cst: bool) -> None:
        self._is_constant = is_cst

    @property
    def is_reentrant(self) -> bool:
        return self._is_reentrant

    @is_reentrant.setter
    def is_reentrant(self, is_reentrant: bool) -> None:
        self._is_reentrant = is_reentrant

    @property
    def write_protection(self) -> Optional[List[str]]:
        return self._write_protection

    @write_protection.setter
    def write_protection(self, write_protection: List[str]) -> None:
        self._write_protection = write_protection

    @property
    def visibility(self) -> Optional[str]:
        """
        str: variable visibility
        """
        return self._visibility

    @visibility.setter
    def visibility(self, v: str) -> None:
        self._visibility = v

    def set_type(self, t: Optional[Union[List, Type, str]]) -> None:
        if isinstance(t, str):
            self._type = ElementaryType(t)
            return
        assert isinstance(t, (Type, list)) or t is None
        self._type = t

    @property
    def is_immutable(self) -> bool:
        """
        Return true of the variable is immutable

        :return:
        """
        return self._is_immutable

    @is_immutable.setter
    def is_immutable(self, immutablility: bool) -> None:
        self._is_immutable = immutablility

    ###################################################################################
    ###################################################################################
    # region Signature
    ###################################################################################
    ###################################################################################

    @property
    def signature(self) -> Tuple[str, List[str], List[str]]:
        """
        Return the signature of the state variable as a function signature
        :return: (str, list(str), list(str)), as (name, list parameters type, list return values type)
        """
        # pylint: disable=import-outside-toplevel
        from slither.utils.type import (
            export_nested_types_from_variable,
            export_return_type_from_variable,
        )

        return (
            self.name,
            [str(x) for x in export_nested_types_from_variable(self)],  # type: ignore
            [str(x) for x in export_return_type_from_variable(self)],  # type: ignore
        )

    @property
    def signature_str(self) -> str:
        """
        Return the signature of the state variable as a function signature
        :return: str: func_name(type1,type2) returns(type3)
        """
        name, parameters, returnVars = self.signature
        return name + "(" + ",".join(parameters) + ") returns(" + ",".join(returnVars) + ")"

    @property
    def solidity_signature(self) -> str:
        name, parameters, _ = self.signature
        return f'{name}({",".join(parameters)})'

    def __str__(self) -> str:
        if self._name is None:
            return ""
        return self._name
