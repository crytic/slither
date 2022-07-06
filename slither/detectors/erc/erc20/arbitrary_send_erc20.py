from typing import List

from slither.core.cfg.node import Node
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.slithir.operations import HighLevelCall, LibraryCall
from slither.core.declarations import Function, SolidityVariableComposed
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations import Call
from slither.slithir.operations import TypeConversion
from slither.slithir.operations.solidity_call import SolidityCall


def constant_propagation(instructions: List[Operation]):
    """Perform a limited constant propagation of `msg.sender` and `address(this)`
    across procedures (internal and library calls).
    """
    mappings = {}
    changed = True
    while changed:
        changed = False
        for instr in instructions:
            if isinstance(instr, Assignment) and instr.rvalue == SolidityVariableComposed(
                "msg.sender"
            ):
                mappings[instr.lvalue] = instr.rvalue
            elif isinstance(instr, TypeConversion) and instr.variable == SolidityVariable("this"):
                mappings[instr.lvalue] = instr.variable

        for (i, instr) in enumerate(instructions):
            # This ignores return values like (x, y) = abi.decode(...)
            if isinstance(instr, Call) and not isinstance(instr, SolidityCall):
                new_args = [mappings.get(x, x) for x in instr.arguments]
                if instr.arguments != new_args:
                    instr.arguments = new_args
                    instructions[i] = instr
                    changed = True


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

    @staticmethod
    def _arbitrary_from(ir: Operation, results: List[Node]):
        """Finds instances of (safe)transferFrom that do not use msg.sender or address(this) as from parameter."""

        if (
            isinstance(ir, HighLevelCall)
            and isinstance(ir.function, Function)
            and ir.function.solidity_signature == "transferFrom(address,address,uint256)"
            and ir.arguments[0]
            not in (SolidityVariableComposed("msg.sender"), SolidityVariable("this"))
        ):
            results.append(ir.node)
        elif (
            isinstance(ir, LibraryCall)
            and ir.function.solidity_signature
            == "safeTransferFrom(address,address,address,uint256)"
            and ir.arguments[1]
            not in (SolidityVariableComposed("msg.sender"), SolidityVariable("this"))
        ):
            results.append(ir.node)

    def _detect_arbitrary_from(self, instructions: List[Operation]):
        has_permit = False
        for ir in instructions:
            if isinstance(ir, InternalCall):
                self.simplify_and_analyze(ir.function.nodes)
            # High level calls (view functions) can also be `StateVariable`
            if isinstance(ir, HighLevelCall) and isinstance(ir.function, Function):
                sig = ir.function.solidity_signature
                has_permit |= sig == "permit(address,address,uint256,uint256,uint8,bytes32,bytes32)"

                if sig in (
                    "transferFrom(address,address,uint256)",
                    "safeTransferFrom(address,address,address,uint256)",
                ):
                    if has_permit:
                        ArbitrarySendErc20._arbitrary_from(ir, self._permit_results)
                    else:
                        ArbitrarySendErc20._arbitrary_from(ir, self._no_permit_results)

    def simplify_and_analyze(self, nodes: List[Node]):
        ir_ssa = []
        for node in nodes:
            for ir in node.irs_ssa:
                ir_ssa.append(ir)

        constant_propagation(ir_ssa)
        self._detect_arbitrary_from(ir_ssa)

    def detect(self):
        """Detect transfers that use arbitrary `from` parameter."""
        for contract in self.compilation_unit.contracts_derived:
            for func in contract.functions_entry_points:
                self.simplify_and_analyze(func.nodes)
