"""
Function module
"""

from typing import TYPE_CHECKING

from slither.core.declarations.contract_level import ContractLevel
from slither.core.declarations import Function
from slither.utils.code_complexity import compute_cyclomatic_complexity


if TYPE_CHECKING:
    from slither.core.declarations import Contract
    from slither.core.scope.scope import FileScope
    from slither.slithir.variables.state_variable import StateIRVariable
    from slither.core.compilation_unit import SlitherCompilationUnit


class FunctionContract(Function, ContractLevel):
    def __init__(self, compilation_unit: "SlitherCompilationUnit") -> None:
        super().__init__(compilation_unit)
        self._contract_declarer: Contract | None = None

    def set_contract_declarer(self, contract: "Contract") -> None:
        self._contract_declarer = contract

    @property
    def contract_declarer(self) -> "Contract":
        """
        Return the contract where this function was declared. Only functions have both a contract, and contract_declarer
        This is because we need to have separate representation of the function depending of the contract's context
        For example a function calling super.f() will generate different IR depending on the current contract's inheritance

        Returns:
            The contract where this function was declared
        """

        assert self._contract_declarer
        return self._contract_declarer

    @property
    def canonical_name(self) -> str:
        """
        str: contract.func_name(type1,type2)
        Return the function signature without the return values
        """
        if self._canonical_name is None:
            name, parameters, _ = self.signature
            self._canonical_name = (
                ".".join([self.contract_declarer.name] + self._internal_scope + [name])
                + "("
                + ",".join(parameters)
                + ")"
            )
        return self._canonical_name

    def is_declared_by(self, contract: "Contract") -> bool:
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract_declarer == contract

    @property
    def file_scope(self) -> "FileScope":
        # This is the contract declarer's file scope because inherited functions have access
        # to the file scope which their declared in. This scope may contain references not
        # available in the child contract's scope. See inherited_function_scope.sol for an example.
        return self.contract_declarer.file_scope

    # endregion
    ###################################################################################
    ###################################################################################
    # region Functions
    ###################################################################################
    ###################################################################################

    @property
    def functions_shadowed(self) -> list["Function"]:
        """
            Return the list of functions shadowed
        Returns:
            list(core.Function)

        """
        candidates = [c.functions_declared for c in self.contract.inheritance]
        candidates = [candidate for sublist in candidates for candidate in sublist]
        return [f for f in candidates if f.full_name == self.full_name]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Summary information
    ###################################################################################
    ###################################################################################

    def get_summary(
        self,
    ) -> tuple[str, str, str, list[str], list[str], list[str], list[str], list[str], int]:
        """
            Return the function summary
        Returns:
            (str, str, str, list(str), list(str), listr(str), list(str), list(str);
            contract_name, name, visibility, modifiers, vars read, vars written, internal_calls, external_calls_as_expressions
        """
        return (
            self.contract_declarer.name,
            self.full_name,
            self.visibility,
            [str(x) for x in self.modifiers],
            [str(x) for x in self.state_variables_read + self.solidity_variables_read],
            [str(x) for x in self.state_variables_written],
            [str(x) for x in self.internal_calls],
            [str(x) for x in self.external_calls_as_expressions],
            compute_cyclomatic_complexity(self),
        )

    # endregion
    ###################################################################################
    ###################################################################################
    # region SlithIr and SSA
    ###################################################################################
    ###################################################################################

    def generate_slithir_ssa(
        self, all_ssa_state_variables_instances: dict[str, "StateIRVariable"]
    ) -> None:
        from slither.slithir.utils.ssa import add_ssa_ir, transform_slithir_vars_to_ssa
        from slither.core.dominators.utils import (
            compute_dominance_frontier,
            compute_dominators,
        )

        compute_dominators(self.nodes)
        compute_dominance_frontier(self.nodes)
        transform_slithir_vars_to_ssa(self)
        if not self.contract.is_incorrectly_constructed:
            add_ssa_ir(self, all_ssa_state_variables_instances)
