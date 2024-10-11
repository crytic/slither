from typing import Optional, TYPE_CHECKING

from slither.core.variables.variable import Variable
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.solidity_types.mapping_type import MappingType
from slither.core.solidity_types.elementary_type import ElementaryType

from slither.core.declarations.structure import Structure

if TYPE_CHECKING:  # type: ignore
    from slither.core.declarations import Function


class LocalVariable(Variable):
    def __init__(self) -> None:
        super().__init__()
        self._location: Optional[str] = None
        self._function: Optional["Function"] = None

    def set_function(self, function: "Function") -> None:
        self._function = function

    @property
    def function(self) -> "Function":
        assert self._function
        return self._function

    def set_location(self, loc: str) -> None:
        self._location = loc

    @property
    def location(self) -> Optional[str]:
        """
            Variable Location
            Can be storage/memory or default
        Returns:
            (str)
        """
        return self._location

    @property
    def is_scalar(self) -> bool:
        return isinstance(self.type, ElementaryType) and not self.is_storage

    @property
    def is_storage(self) -> bool:
        """
            Return true if the variable is located in storage
            See https://solidity.readthedocs.io/en/v0.4.24/types.html?highlight=storage%20location#data-location
        Returns:
            (bool)
        """
        # pylint: disable=import-outside-toplevel
        from slither.core.solidity_types.array_type import ArrayType

        if self.location == "memory":
            return False
        if self.location == "calldata":
            return False
        # Use by slithIR SSA
        if self.location == "reference_to_storage":
            return False
        if self.location == "storage":
            return True

        if isinstance(self.type, (ArrayType, MappingType)):
            return True

        if isinstance(self.type, UserDefinedType):
            return isinstance(self.type.type, Structure)

        return False

    @property
    def canonical_name(self) -> str:
        return f"{self.function.canonical_name}.{self.name}"
