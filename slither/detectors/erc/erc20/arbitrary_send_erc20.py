from typing import List
from slither.core.cfg.node import Node
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.slithir.operations import HighLevelCall, LibraryCall
from slither.core.declarations import Contract, Function, SolidityVariableComposed
from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.compilation_unit import SlitherCompilationUnit


class ArbitrarySendErc20:
    """Detects instances where ERC20 can be sent from an arbitrary from address."""

    def __init__(self, compilation_unit: SlitherCompilationUnit):
        self._compilation_unit = compilation_unit
        self._no_permit_results: List[Node] = []
        self._permit_results: List[Node] = []

    @property
    def compilation_unit(self) -> SlitherCompilationUnit:
        return self._compilation_unit

    @property
    def no_permit_results(self) -> List[Node]:
        return self._no_permit_results

    @property
    def permit_results(self) -> List[Node]:
        return self._permit_results

    def _detect_arbitrary_from(self, contract: Contract):
        for f in contract.functions:
            all_high_level_calls = [
                f_called[1].solidity_signature
                for f_called in f.high_level_calls
                if isinstance(f_called[1], Function)
            ]
            all_library_calls = [f_called[1].solidity_signature for f_called in f.library_calls]
            if (
                "transferFrom(address,address,uint256)" in all_high_level_calls
                or "safeTransferFrom(address,address,address,uint256)" in all_library_calls
            ):
                if (
                    "permit(address,address,uint256,uint256,uint8,bytes32,bytes32)"
                    in all_high_level_calls
                ):
                    ArbitrarySendErc20._arbitrary_from(f.nodes, self._permit_results)
                else:
                    ArbitrarySendErc20._arbitrary_from(f.nodes, self._no_permit_results)

    @staticmethod
    def _arbitrary_from(nodes: List[Node], results: List[Node]):
        """Finds instances of (safe)transferFrom that do not use msg.sender or address(this) as from parameter."""
        for node in nodes:
            for ir in node.irs:
                if (
                    isinstance(ir, HighLevelCall)
                    and isinstance(ir.function, Function)
                    and ir.function.solidity_signature == "transferFrom(address,address,uint256)"
                    and not (
                        is_dependent(
                            ir.arguments[0],
                            SolidityVariableComposed("msg.sender"),
                            node.function.contract,
                        )
                        or is_dependent(
                            ir.arguments[0],
                            SolidityVariable("this"),
                            node.function.contract,
                        )
                    )
                ):
                    results.append(ir.node)
                elif (
                    isinstance(ir, LibraryCall)
                    and ir.function.solidity_signature
                    == "safeTransferFrom(address,address,address,uint256)"
                    and not (
                        is_dependent(
                            ir.arguments[1],
                            SolidityVariableComposed("msg.sender"),
                            node.function.contract,
                        )
                        or is_dependent(
                            ir.arguments[1],
                            SolidityVariable("this"),
                            node.function.contract,
                        )
                    )
                ):
                    results.append(ir.node)

    def detect(self):
        """Detect transfers that use arbitrary `from` parameter."""
        for c in self.compilation_unit.contracts_derived:
            self._detect_arbitrary_from(c)
