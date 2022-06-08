from typing import List

from attr import has
from slither.core.cfg.node import Node
from slither.core.declarations.function_contract import FunctionContract
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.slithir.operations import HighLevelCall, LibraryCall
from slither.core.declarations import Contract, Function, SolidityVariableComposed
from slither.analyses.data_dependency.data_dependency import always_depends_on
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.slithir.operations.operation import Operation


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
        for func in contract.functions_entry_points:
            has_permit = False
            for node in func.nodes:
                for ir in node.all_slithir_operations():
                    # FIXME this is not always in the same order and produces causes permits to fall into non-permit
                    if isinstance(ir, HighLevelCall):
                        sig = ir.function.solidity_signature
                        has_permit |= (
                            sig == "permit(address,address,uint256,uint256,uint8,bytes32,bytes32)"
                        )

                        if sig in (
                            "transferFrom(address,address,uint256)",
                            "safeTransferFrom(address,address,address,uint256)",
                        ):
                            print(has_permit)
                            if has_permit:
                                ArbitrarySendErc20._arbitrary_from(func, ir, self._permit_results)
                            else:
                                ArbitrarySendErc20._arbitrary_from(
                                    func, ir, self._no_permit_results
                                )

    @staticmethod
    def _arbitrary_from(func: FunctionContract, ir: Operation, results: List[Node]):
        """Finds instances of (safe)transferFrom that do not use msg.sender or address(this) as from parameter."""
        if (
            isinstance(ir, HighLevelCall)
            and isinstance(ir.function, Function)
            and ir.function.solidity_signature == "transferFrom(address,address,uint256)"
            and not (
                always_depends_on(
                    ir.arguments[0],
                    SolidityVariableComposed("msg.sender"),
                    ir.node.function,
                )
                or always_depends_on(
                    ir.arguments[0],
                    SolidityVariable("this"),
                    ir.node.function,
                )
            )
        ):
            results.append((func, ir.node.function))
        elif (
            isinstance(ir, LibraryCall)
            and ir.function.solidity_signature
            == "safeTransferFrom(address,address,address,uint256)"
            and not (
                always_depends_on(
                    ir.arguments[1],
                    SolidityVariableComposed("msg.sender"),
                    ir.node.function,
                )
                or always_depends_on(
                    ir.arguments[1],
                    SolidityVariable("this"),
                    ir.node.function,
                )
            )
        ):
            results.append((func, ir.node.function))

    def detect(self):
        """Detect transfers that use arbitrary `from` parameter."""
        for c in self.compilation_unit.contracts_derived:
            self._detect_arbitrary_from(c)
