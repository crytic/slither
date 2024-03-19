"""
    Function module
"""
from typing import Dict, List, Tuple, TYPE_CHECKING, Union, Optional

from slither.core.declarations import Function
from slither.core.declarations.top_level import TopLevel
from slither.core.solidity_types.type import Type

if TYPE_CHECKING:
    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.core.scope.scope import FileScope
    from slither.slithir.variables.state_variable import StateIRVariable

USING_FOR_KEY = Union[str, Type]
USING_FOR_ITEM = List[Union[Type, Function]]


class FunctionTopLevel(Function, TopLevel):
    def __init__(self, compilation_unit: "SlitherCompilationUnit", scope: "FileScope") -> None:
        super().__init__(compilation_unit)
        self._scope: "FileScope" = scope
        self._using_for_complete: Optional[Dict[USING_FOR_KEY, USING_FOR_ITEM]] = None

    @property
    def file_scope(self) -> "FileScope":
        return self._scope

    @property
    def using_for_complete(self) -> Dict[USING_FOR_KEY, USING_FOR_ITEM]:
        """
        Dict[Union[str, Type], List[Type]]: Dict of merged local using for directive with top level directive
        """

        def _merge_using_for(
            uf1: Dict[USING_FOR_KEY, USING_FOR_ITEM], uf2: Dict[USING_FOR_KEY, USING_FOR_ITEM]
        ) -> Dict[USING_FOR_KEY, USING_FOR_ITEM]:
            result = {**uf1, **uf2}
            for key, value in result.items():
                if key in uf1 and key in uf2:
                    result[key] = value + uf1[key]
            return result

        if self._using_for_complete is None:
            result = {}
            for uftl in self.file_scope.using_for_directives:
                result = _merge_using_for(result, uftl.using_for)
            self._using_for_complete = result
        return self._using_for_complete

    @property
    def canonical_name(self) -> str:
        """
        str: contract.func_name(type1,type2)
        Return the function signature without the return values
        """
        if self._canonical_name is None:
            name, parameters, _ = self.signature
            self._canonical_name = (
                ".".join(self._internal_scope + [name]) + "(" + ",".join(parameters) + ")"
            )
        return self._canonical_name

    # endregion
    ###################################################################################
    ###################################################################################
    # region Functions
    ###################################################################################
    ###################################################################################

    @property
    def functions_shadowed(self) -> List["Function"]:
        return []

    # endregion
    ###################################################################################
    ###################################################################################
    # region Summary information
    ###################################################################################
    ###################################################################################

    def get_summary(
        self,
    ) -> Tuple[str, str, str, List[str], List[str], List[str], List[str], List[str]]:
        """
            Return the function summary
        Returns:
            (str, str, str, list(str), list(str), listr(str), list(str), list(str);
            contract_name, name, visibility, modifiers, vars read, vars written, internal_calls, external_calls_as_expressions
        """
        return (
            "",
            self.full_name,
            self.visibility,
            [str(x) for x in self.modifiers],
            [str(x) for x in self.state_variables_read + self.solidity_variables_read],
            [str(x) for x in self.state_variables_written],
            [str(x) for x in self.internal_calls],
            [str(x) for x in self.external_calls_as_expressions],
        )

    # endregion
    ###################################################################################
    ###################################################################################
    # region SlithIr and SSA
    ###################################################################################
    ###################################################################################

    def generate_slithir_ssa(
        self, all_ssa_state_variables_instances: Dict[str, "StateIRVariable"]
    ) -> None:
        # pylint: disable=import-outside-toplevel
        from slither.slithir.utils.ssa import add_ssa_ir, transform_slithir_vars_to_ssa
        from slither.core.dominators.utils import (
            compute_dominance_frontier,
            compute_dominators,
        )

        compute_dominators(self.nodes)
        compute_dominance_frontier(self.nodes)
        transform_slithir_vars_to_ssa(self)

        add_ssa_ir(self, all_ssa_state_variables_instances)
