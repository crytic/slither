from typing import Union, Any, TYPE_CHECKING

from slither.core.expressions.expression import Expression
from slither.core.expressions.literal import Literal
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.type import Type
from slither.visitors.expression.constants_folding import ConstantFolding

if TYPE_CHECKING:
    from slither.core.expressions.binary_operation import BinaryOperation
    from slither.core.expressions.identifier import Identifier


class ArrayType(Type):
    def __init__(
        self,
        t: Type,
        length: Union["Identifier", Literal, "BinaryOperation", int] | None,
    ) -> None:
        assert isinstance(t, Type)
        if length:
            if isinstance(length, int):
                length = Literal(length, ElementaryType("uint256"))

        super().__init__()
        self._type: Type = t
        assert length is None or isinstance(length, Expression)
        self._length: Expression | None = length

        if length:
            if not isinstance(length, Literal):
                cf = ConstantFolding(length, "uint256")
                length = cf.result()
            self._length_value: Literal | None = length
        else:
            self._length_value = None

    @property
    def type(self) -> Type:
        return self._type

    @property
    def is_dynamic(self) -> bool:
        return self.length is None

    @property
    def length(self) -> Expression | None:
        return self._length

    @property
    def length_value(self) -> Literal | None:
        return self._length_value

    @property
    def is_fixed_array(self) -> bool:
        return bool(self.length)

    @property
    def is_dynamic_array(self) -> bool:
        return not self.is_fixed_array

    @property
    def storage_size(self) -> tuple[int, bool]:
        if self._length_value:
            elem_size, _ = self._type.storage_size
            return elem_size * int(str(self._length_value)), True
        return 32, True

    def __str__(self) -> str:
        if self._length:
            return str(self._type) + f"[{self._length_value!s}]"
        return str(self._type) + "[]"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ArrayType):
            return False
        return self._type == other.type and self._length_value == other.length_value

    def __hash__(self) -> int:
        return hash(str(self))
