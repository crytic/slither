"""
Detector for singly-hashed Merkle leaves when using OpenZeppelin's MerkleProof library.

This detector identifies potential second preimage attacks on Merkle trees where
a leaf is passed to MerkleProof.verify/verifyCalldata/processProof/processProofCalldata
without being double-hashed (hash of hash).

Reference: https://www.rareskills.io/post/merkle-tree-second-preimage-attack
"""

from slither.core.cfg.node import Node
from slither.core.declarations import Contract, Function, SolidityFunction
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import SolidityCall, InternalCall
from slither.slithir.variables import Constant
from slither.utils.output import Output

# MerkleProof functions and the index of their leaf parameter
MERKLE_PROOF_FUNCTIONS = {
    "verify": 2,  # verify(bytes32[] proof, bytes32 root, bytes32 leaf)
    "verifyCalldata": 2,  # verifyCalldata(bytes32[] proof, bytes32 root, bytes32 leaf)
    "processProof": 1,  # processProof(bytes32[] proof, bytes32 leaf)
    "processProofCalldata": 1,  # processProofCalldata(bytes32[] proof, bytes32 leaf)
    "multiProofVerify": 2,  # multiProofVerify(..., bytes32 root, bytes32[] leaves, ...)
    "multiProofVerifyCalldata": 2,
}

KECCAK_FUNCTIONS = (
    SolidityFunction("keccak256()"),
    SolidityFunction("keccak256(bytes)"),
)


def _count_keccak_in_function(func: Function, visited_funcs: set | None = None) -> int:
    """
    Count the minimum keccak256 applications in a function's return path.
    This helps track hashing through helper functions.
    """
    if visited_funcs is None:
        visited_funcs = set()

    if func in visited_funcs:
        return 0
    visited_funcs.add(func)

    max_count = 0
    for node in func.nodes:
        for ir in node.irs:
            if isinstance(ir, SolidityCall) and ir.function in KECCAK_FUNCTIONS:
                # Found a keccak call, check if its result flows to return
                count = 1 + _count_keccak_for_variable(
                    ir.arguments[0] if ir.arguments else None,
                    node,
                    visited_funcs.copy(),
                )
                max_count = max(max_count, count)

    return max_count


def _count_keccak_for_variable(
    variable,
    node: Node,
    visited_funcs: set | None = None,
    visited_vars: set | None = None,
) -> int:
    """
    Count how many keccak256 operations were applied to produce this variable.
    Uses backward traversal through the CFG to find the hash chain.
    Also follows internal function calls to track hashing in helper functions.

    Returns the number of keccak256 applications found.
    """
    if visited_funcs is None:
        visited_funcs = set()
    if visited_vars is None:
        visited_vars = set()

    if variable is None or isinstance(variable, Constant):
        return 0

    # Avoid infinite loops on variables
    var_id = id(variable)
    if var_id in visited_vars:
        return 0
    visited_vars.add(var_id)

    # Search current node and predecessor nodes
    nodes_to_check = [node]
    nodes_visited: set[Node] = set()

    while nodes_to_check:
        current_node = nodes_to_check.pop(0)
        if current_node in nodes_visited:
            continue
        nodes_visited.add(current_node)

        # Check all IR operations in this node (in reverse order for assignments)
        for ir in current_node.irs:
            # Check if this IR produces our variable
            if not hasattr(ir, "lvalue") or ir.lvalue != variable:
                continue

            # Check if it's a keccak256 call
            if isinstance(ir, SolidityCall) and ir.function in KECCAK_FUNCTIONS:
                if ir.arguments:
                    arg = ir.arguments[0]
                    return 1 + _count_keccak_for_variable(
                        arg, current_node, visited_funcs, visited_vars
                    )
                return 1

            # Check if it's an internal function call - trace into the function
            if isinstance(ir, InternalCall) and isinstance(ir.function, Function):
                called_func = ir.function
                if called_func not in visited_funcs:
                    count = _count_keccak_in_function(called_func, visited_funcs)
                    if count > 0:
                        return count

            # Check if it's an assignment from another variable
            if hasattr(ir, "read"):
                for read_var in ir.read:
                    if read_var != variable and not isinstance(read_var, Constant):
                        count = _count_keccak_for_variable(
                            read_var, current_node, visited_funcs, visited_vars
                        )
                        if count > 0:
                            return count

        # Add predecessor nodes to check
        for father in current_node.fathers:
            if father not in nodes_visited:
                nodes_to_check.append(father)

    return 0


def _find_merkle_proof_calls(contract: Contract) -> list[tuple[Node, str, int]]:
    """
    Find all calls to MerkleProof library functions in the contract.

    Returns list of tuples: (node, function_name, keccak_count)
    """
    results = []

    for ir in contract.all_library_calls:
        # Check if this is a MerkleProof library call
        dest = ir.destination
        if not hasattr(dest, "name") or dest.name != "MerkleProof":
            continue

        func_name = str(ir.function_name)
        if func_name not in MERKLE_PROOF_FUNCTIONS:
            continue

        # Get the leaf parameter index
        leaf_index = MERKLE_PROOF_FUNCTIONS[func_name]

        # Get the leaf argument
        if ir.arguments and len(ir.arguments) > leaf_index:
            leaf_arg = ir.arguments[leaf_index]

            # Count keccak256 applications
            keccak_count = _count_keccak_for_variable(leaf_arg, ir.node)

            if keccak_count < 2:
                results.append((ir.node, func_name, keccak_count))

    return results


class MerkleSinglyHashedLeaf(AbstractDetector):
    """
    Detect potential second preimage attacks on Merkle trees when using
    OpenZeppelin's MerkleProof library with insufficiently hashed leaves.
    """

    ARGUMENT = "merkle-singly-hashed-leaf"
    HELP = "Merkle leaf not double-hashed"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation"
        "#merkle-tree-second-preimage-attack"
    )

    WIKI_TITLE = "Merkle Tree Second Preimage Attack"
    WIKI_DESCRIPTION = (
        "Detects when a leaf passed to OpenZeppelin's MerkleProof.verify or related "
        "functions is not double-hashed (hash of hash). Without double hashing, the "
        "Merkle tree is vulnerable to second preimage attacks where an attacker can "
        "forge proofs by presenting an intermediate node as a leaf."
    )

    WIKI_EXPLOIT_SCENARIO = """
```solidity
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";

contract Airdrop {
    bytes32 public merkleRoot;

    // BAD: leaf is only hashed once
    function claim(bytes32[] calldata proof, address account, uint256 amount) external {
        bytes32 leaf = keccak256(abi.encodePacked(account, amount));
        require(MerkleProof.verify(proof, merkleRoot, leaf), "Invalid proof");
        // ... distribute tokens
    }
}
```
An attacker who knows an intermediate node value (which is 64 bytes - two concatenated hashes) can craft a shorter proof that the contract will accept as valid, potentially claiming tokens they're not entitled to."""

    WIKI_RECOMMENDATION = """Double-hash the leaf data before passing it to MerkleProof functions:
```solidity
// GOOD: leaf is double-hashed
bytes32 leaf = keccak256(bytes.concat(keccak256(abi.encodePacked(account, amount))));
require(MerkleProof.verify(proof, merkleRoot, leaf), "Invalid proof");
```

Alternatively, use OpenZeppelin's `MerkleProof.verify` with leaves that are already double-hashed when building the tree off-chain."""

    def _detect(self) -> list[Output]:
        results: list[Output] = []

        for contract in self.compilation_unit.contracts_derived:
            findings = _find_merkle_proof_calls(contract)

            for node, func_name, keccak_count in findings:
                if keccak_count == 0:
                    hash_msg = "without any hashing"
                else:
                    hash_msg = "with only single hashing"

                info: DETECTOR_INFO = [
                    "MerkleProof.",
                    func_name,
                    "() is called ",
                    hash_msg,
                    " on the leaf in ",
                    node.function,
                    "\n\t- ",
                    node,
                    "\n",
                ]
                res = self.generate_result(info)
                results.append(res)

        return results
