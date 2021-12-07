import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.solc_parsing.slither_compilation_unit_solc import SlitherCompilationUnitSolc


class CallerContextExpression(metaclass=abc.ABCMeta):
    """
    This class is inherited by all the declarations class that can be used in the expression/type parsing
    As a source of context/scope

    It is used by any declaration class that can be top-level and require complex parsing

    """

    @property
    @abc.abstractmethod
    def is_compact_ast(self) -> bool:
        pass

    @property
    @abc.abstractmethod
    def compilation_unit(self) -> "SlitherCompilationUnit":
        pass

    @abc.abstractmethod
    def get_key(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def slither_parser(self) -> "SlitherCompilationUnitSolc":
        pass
