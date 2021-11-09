"""
    Function module
"""
from typing import List, Tuple

from slither.core.declarations import Function
from slither.core.declarations.top_level import TopLevel


class FunctionTopLevel(Function, TopLevel):
    @property
    def canonical_name(self) -> str:
        """
        str: contract.func_name(type1,type2)
        Return the function signature without the return values
        """
        if self._canonical_name is None:
            name, parameters, _ = self.signature
            self._canonical_name = ".".join(self._scope + [name]) + "(" + ",".join(parameters) + ")"
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

    def generate_slithir_ssa(self, all_ssa_state_variables_instances):
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
