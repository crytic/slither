from typing import TYPE_CHECKING, Dict

from slither.core.declarations.custom_error import CustomError
from slither.core.declarations.custom_error_contract import CustomErrorContract
from slither.core.declarations.custom_error_top_level import CustomErrorTopLevel
from slither.core.variables.local_variable import LocalVariable
from slither.solc_parsing.declarations.caller_context import CallerContextExpression
from slither.solc_parsing.variables.local_variable import LocalVariableSolc
from slither.solc_parsing.ast.types import ErrorDefinition, ParameterList, VariableDeclaration

if TYPE_CHECKING:
    from slither.solc_parsing.slither_compilation_unit_solc import SlitherCompilationUnitSolc
    from slither.core.compilation_unit import SlitherCompilationUnit


# Part of the code was copied from the function parsing
# In the long term we should refactor these two classes to merge the duplicated code


class CustomErrorSolc(CallerContextExpression):
    def __init__(
        self,
        custom_error: CustomError,
        custom_error_def: ErrorDefinition,
        slither_parser: "SlitherCompilationUnitSolc",
    ):
        self._slither_parser: "SlitherCompilationUnitSolc" = slither_parser
        self._custom_error = custom_error
        custom_error.name = custom_error_def.name
        self._params_was_analyzed = False
        self._custom_error_def = custom_error_def

    def analyze_params(self):
        # Can be re-analyzed due to inheritance
        if self._params_was_analyzed:
            return
        self._params_was_analyzed = True

        if self._custom_error_def.params:
            self._parse_params(self._custom_error_def.params)

    def _parse_params(self, params: ParameterList):
        for param in params.params:
            local_var = self._add_param(param)
            self._custom_error.add_parameters(local_var.underlying_variable)

        self._custom_error.set_solidity_sig()

    def _add_param(self, param: VariableDeclaration) -> LocalVariableSolc:

        local_var = LocalVariable()
        local_var.set_offset(param.src, self._slither_parser.compilation_unit)

        local_var_parser = LocalVariableSolc(local_var, param)

        if isinstance(self._custom_error, CustomErrorTopLevel):
            local_var_parser.analyze(self)
        else:
            assert isinstance(self._custom_error, CustomErrorContract)
            local_var_parser.analyze(self)

        # see https://solidity.readthedocs.io/en/v0.4.24/types.html?highlight=storage%20location#data-location
        if local_var.location == "default":
            local_var.set_location("memory")

        return local_var_parser

    @property
    def underlying_custom_error(self) -> CustomError:
        return self._custom_error

    @property
    def slither_parser(self) -> "SlitherCompilationUnitSolc":
        return self._slither_parser

    @property
    def compilation_unit(self) -> "SlitherCompilationUnit":
        return self._custom_error.compilation_unit
