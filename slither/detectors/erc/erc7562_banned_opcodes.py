"""
Module detecting ERC-7562 banned opcodes reachable from ERC-4337 validation functions
"""

from collections import deque
from dataclasses import dataclass, field
from typing import NamedTuple

from slither.core.cfg.node import Node
from slither.core.declarations import Contract, Function
from slither.core.declarations.function_contract import FunctionContract
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class BannedOpcode(NamedTuple):
    name: str
    rule: str


BANNED = "banned by ERC-7562 OP-011"
STAKED_ONLY = "allowed by ERC-7562 OP-080 only if the entity is staked"

TIMESTAMP = BannedOpcode("TIMESTAMP", BANNED)
NUMBER = BannedOpcode("NUMBER", BANNED)
COINBASE = BannedOpcode("COINBASE", BANNED)
PREVRANDAO = BannedOpcode("PREVRANDAO", BANNED)
GASLIMIT = BannedOpcode("GASLIMIT", BANNED)
BASEFEE = BannedOpcode("BASEFEE", BANNED)
BLOBBASEFEE = BannedOpcode("BLOBBASEFEE", BANNED)
ORIGIN = BannedOpcode("ORIGIN", BANNED)
GASPRICE = BannedOpcode("GASPRICE", BANNED)
BLOCKHASH = BannedOpcode("BLOCKHASH", BANNED)
BLOBHASH = BannedOpcode("BLOBHASH", BANNED)
SELFDESTRUCT = BannedOpcode("SELFDESTRUCT", BANNED)
BALANCE = BannedOpcode("BALANCE", STAKED_ONLY)

# Global variables, keyed on the SolidityVariable name
BANNED_VARIABLES: dict[str, BannedOpcode] = {
    "now": TIMESTAMP,
    "block.timestamp": TIMESTAMP,
    "block.number": NUMBER,
    "block.coinbase": COINBASE,
    "block.difficulty": PREVRANDAO,
    "block.prevrandao": PREVRANDAO,
    "block.gaslimit": GASLIMIT,
    "block.basefee": BASEFEE,
    "block.blobbasefee": BLOBBASEFEE,
    "tx.origin": ORIGIN,
    "tx.gasprice": GASPRICE,
}

# Builtin calls, keyed on the SolidityFunction name. Inline assembly builtins carry the
# uint256 signatures assigned in slither.solc_parsing.yul.evm_functions. SELFBALANCE has no
# entry: Slither lowers both selfbalance() and address(this).balance to balance(address), so it
# is reported as BALANCE, which OP-080 treats the same way
BANNED_CALLS: dict[str, BannedOpcode] = {
    "blockhash(uint256)": BLOCKHASH,
    "blobhash(uint256)": BLOBHASH,
    "selfdestruct(address)": SELFDESTRUCT,
    "suicide(address)": SELFDESTRUCT,
    "balance(address)": BALANCE,
    "timestamp()": TIMESTAMP,
    "number()": NUMBER,
    "coinbase()": COINBASE,
    "difficulty()": PREVRANDAO,
    "prevrandao()": PREVRANDAO,
    "gaslimit()": GASLIMIT,
    "basefee()": BASEFEE,
    "blobbasefee()": BLOBBASEFEE,
    "origin()": ORIGIN,
    "gasprice()": GASPRICE,
    "balance(uint256)": BALANCE,
    "selfdestruct(uint256)": SELFDESTRUCT,
}

# Not covered: GAS is allowed immediately before a *CALL (OP-012), CREATE is allowed when the
# operation carries a factory (OP-032) and CREATE2 once in the factory frame (OP-031). Telling
# the permitted uses apart needs data flow, and flagging every gasleft() would make the
# detector unusable. EXTCODE* and *CALL rules (OP-041 to OP-062) depend on the callee's
# deployment state, which is not visible statically.

ENTRY_POINTS = ("validateUserOp", "validatePaymasterUserOp")


@dataclass
class _Finding:
    """
    One (validation entry point, opcode) pair: the deployable contracts whose validation
    reaches the opcode and the nodes where it is used
    """

    entry: Function
    opcode: BannedOpcode
    contracts: list[Contract] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)


def _is_deployable(contract: Contract) -> bool:
    """
    Interfaces, libraries and abstract contracts never run validation themselves.
    Before Solidity 0.6 a contract with an unimplemented function is abstract without the keyword.
    """
    if contract.is_interface or contract.is_library or contract.is_abstract:
        return False
    return contract.is_fully_implemented


def _validation_entry_points(contract: Contract) -> list[FunctionContract]:
    """
    Match by name rather than by IAccount/IPaymaster inheritance: a contract that declares its
    own interface with the wrong argument list is still what the EntryPoints calls
    """
    return [f for f in contract.functions_entry_points if f.name in ENTRY_POINTS]


def _callees(function: Function) -> list[Function]:
    """
    Functions that run inside the validation frame: internal calls, library calls and modifiers.
    """
    callees: list[Function] = []
    for ir in function.internal_calls + function.library_calls:
        if isinstance(ir.function, Function):
            callees.append(ir.function)
    for modifier in function.modifiers:
        if isinstance(modifier, Function):
            callees.append(modifier)
    return callees


def _reachable_from(entry: Function) -> list[Function]:
    """
    Breadth-first walk over the internal call graph, entry point first
    """
    reachable = [entry]
    queue = deque([entry])
    while queue:
        for callee in _callees(queue.popleft()):
            if callee not in reachable:
                reachable.append(callee)
                queue.append(callee)
    return reachable


def _banned_uses(function: Function) -> list[tuple[Node, BannedOpcode]]:
    uses: list[tuple[Node, BannedOpcode]] = []
    for node in function.nodes:
        for variable in node.solidity_variables_read:
            if variable.name in BANNED_VARIABLES:
                uses.append((node, BANNED_VARIABLES[variable.name]))
        for ir in node.solidity_calls:
            if ir.function.name in BANNED_CALLS:
                uses.append((node, BANNED_CALLS[ir.function.name]))
    return uses


def _same_location(a: Node, b: Node) -> bool:
    return (
        a.source_mapping.filename.absolute == b.source_mapping.filename.absolute
        and a.source_mapping.start == b.source_mapping.start
    )


class ERC7562BannedOpcodes(AbstractDetector):
    """
    Detect ERC-7562 banned opcodes reachable from ERC-4337 validation functions
    """

    ARGUMENT = "erc7562-banned-opcodes"
    HELP = "Banned opcodes reachable from ERC-4337 validation functions"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#erc-7562-banned-opcodes"

    WIKI_TITLE = "ERC-7562 banned opcodes"
    WIKI_DESCRIPTION = """ERC-4337 bundlers simulate `validateUserOp` and `validatePaymasterUserOp` before including a user operation and drop the operation if the simulation reaches an opcode whose result can differ between simulation and inclusion (ERC-7562 rule OP-011): `TIMESTAMP`, `NUMBER`, `ORIGIN`, `GASPRICE`, `COINBASE`, `PREVRANDAO`, `GASLIMIT`, `BASEFEE`, `BLOCKHASH`, `BLOBHASH`, `BLOBBASEFEE` and `SELFDESTRUCT`. `BALANCE` and `SELFBALANCE` are allowed only for staked entities (OP-080).
Nothing on-chain enforces these rules. A contract that breaks them compiles, passes tests that call `EntryPoint.handleOps` directly, and is then rejected by every bundler once deployed. The detector reports each banned opcode reachable from a validation function through internal calls, library calls and modifiers, for every deployable contract."""

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Paymaster is IPaymaster {
    function validatePaymasterUserOp(PackedUserOperation calldata userOp, bytes32, uint256 maxCost)
        external returns (bytes memory context, uint256 validationData)
    {
        context = abi.encode(userOp.sender, maxCost, block.timestamp);
        validationData = _packValidationData(false, uint48(block.timestamp + 1 days), uint48(block.timestamp));
    }
}
```
`Paymaster` reads `block.timestamp` during validation. Every test that calls `EntryPoint.handleOps` passes, but bundlers reject each user operation that names the paymaster, so it cannot sponsor anything in production."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """Remove the banned opcode from every path the validation function can reach, including modifiers and library calls. Express time bounds through the `validAfter` and `validUntil` fields of the returned `validationData` and let the EntryPoint enforce them. Identify the caller with `msg.sender` rather than `tx.origin`. If validation must read a balance, stake the entity with the EntryPoint."""

    def _detect(self) -> list[Output]:
        findings: dict[tuple[str, BannedOpcode], _Finding] = {}
        for contract in self.compilation_unit.contracts:
            if not _is_deployable(contract):
                continue
            for entry in _validation_entry_points(contract):
                self._collect(findings, contract, entry)
        return [self._result(finding) for finding in findings.values()]

    @staticmethod
    def _collect(
        findings: dict[tuple[str, BannedOpcode], _Finding],
        contract: Contract,
        entry: FunctionContract,
    ) -> None:
        """
        Every contract owns a copy of each inherited function, so an inherited entry point
        reaches the same source line once per contract in the hierarchy. Merge on the declaring
        function and the node location, and keep the list of contracts that reach it
        """
        for function in _reachable_from(entry):
            for node, opcode in _banned_uses(function):
                key = (entry.canonical_name, opcode)
                finding = findings.setdefault(key, _Finding(entry, opcode))
                if contract not in finding.contracts:
                    finding.contracts.append(contract)
                if not any(_same_location(node, seen) for seen in finding.nodes):
                    finding.nodes.append(node)

    def _result(self, finding: _Finding) -> Output:
        contracts = ", ".join(contract.name for contract in finding.contracts)
        info: DETECTOR_INFO = [
            finding.entry,
            " reaches ",
            finding.opcode.name,
            " (",
            finding.opcode.rule,
            ") during validation of ",
            contracts,
            ":\n",
        ]
        for node in finding.nodes:
            info += ["\t- ", node, "\n"]
        return self.generate_result(info)
