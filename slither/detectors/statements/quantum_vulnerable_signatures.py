"""
Module detecting the usage of quantum-vulnerable signature verification schemes
"""

from slither.core.cfg.node import Node
from slither.core.declarations import Contract, SolidityFunction
from slither.core.declarations.function_contract import FunctionContract
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import InternalCall, LibraryCall
from slither.utils.output import Output


class QuantumVulnerableSignatures(AbstractDetector):
    """
    Detect the usage of secp256k1 ECDSA signature verification (`ecrecover` or
    OpenZeppelin's `ECDSA.recover`), which is not resistant to
    cryptographically-relevant quantum computers (CRQC).
    """

    ARGUMENT = "quantum-vulnerable-signatures"
    HELP = "Usage of quantum-vulnerable signature verification (`ecrecover` / `ECDSA.recover`)"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#quantum-vulnerable-signature-scheme"

    WIKI_TITLE = "Quantum-vulnerable signature scheme"
    WIKI_DESCRIPTION = (
        "The contract relies on secp256k1 ECDSA signature verification (`ecrecover` or "
        "OpenZeppelin's `ECDSA.recover`). ECDSA-based signatures are not resistant to "
        "cryptographically-relevant quantum computers (CRQC), as Shor's algorithm recovers "
        "the private key from public keys/signatures. This does not indicate a bug: even a "
        "fully correct `ecrecover` usage remains forgeable in the long run."
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract VestingWallet {
    function claim(bytes32 claimHash, uint8 v, bytes32 r, bytes32 s) external {
        require(ecrecover(claimHash, v, r, s) == msg.sender, "invalid signature");
        // release vested funds
    }
}
```
The authorization of `claim` relies on an ECDSA (secp256k1) signature check. Once a
cryptographically-relevant quantum computer exists, previously seen signatures allow
recovery of the underlying private key, and any signature can be forged. Protocol teams
planning long-term security should evaluate post-quantum signature schemes (e.g. NIST
FIPS 204 ML-DSA) and follow migration guidance such as the one tracked by the Ethereum
Foundation's post-quantum team (pq.ethereum.org)."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "Track contract entry points that rely on ECDSA signatures as part of a "
        "post-quantum migration plan. Consider adopting post-quantum or hybrid signature "
        "schemes for long-lived security guarantees (see the NIST post-quantum standards "
        "and https://pq.ethereum.org)."
    )

    @staticmethod
    def _is_ecdsa_recover(function: FunctionContract) -> bool:
        """
        Check if the function is OpenZeppelin's `ECDSA.recover` (matched by the
        declaring contract name `ECDSA` and the function name `recover`).
        """
        return (
            isinstance(function, FunctionContract)
            and function.name == "recover"
            and function.contract_declarer is not None
            and function.contract_declarer.name == "ECDSA"
        )

    # Solidity built-in precompile wrapper (see SOLIDITY_FUNCTIONS in solidity_variables.py)
    ECRECOVER = SolidityFunction("ecrecover(bytes32,uint8,bytes32,bytes32)")

    def _detect_ecdsa_usage(self, contract: Contract) -> list[tuple[FunctionContract, list[Node]]]:
        ret: list[tuple[FunctionContract, list[Node]]] = []
        for function in contract.functions_and_modifiers_declared:
            nodes: list[Node] = []
            for ir in function.solidity_calls:
                if ir.function == self.ECRECOVER:
                    nodes.append(ir.node)
            for ir in function.internal_calls:
                if self._is_ecdsa_recover(ir.function):
                    nodes.append(ir.node)
            for ir in function.library_calls:
                if self._is_ecdsa_recover(ir.function):
                    nodes.append(ir.node)
            if nodes:
                # sort the nodes to get deterministic results
                nodes.sort(key=lambda x: x.node_id)
                ret.append((function, nodes))
        return ret

    def _detect(self) -> list[Output]:
        """Detect the functions that use quantum-vulnerable signature verification"""
        results: list[Output] = []
        for contract in self.compilation_unit.contracts_derived:
            for function, nodes in self._detect_ecdsa_usage(contract):
                info: DETECTOR_INFO = [
                    function,
                    " relies on a quantum-vulnerable signature scheme (secp256k1 ECDSA):\n",
                ]

                for node in nodes:
                    info += ["\t- ", node, "\n"]

                res = self.generate_result(info)
                results.append(res)

        return results
