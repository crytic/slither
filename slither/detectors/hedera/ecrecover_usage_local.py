"""
Detector to find instances where `ecrecover` is used in Solidity contracts.
"""
from slither.core.declarations import Contract
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import Node
from slither.slithir.operations import SolidityCall
from slither.utils.output import Output
from slither.core.declarations import SolidityFunction

class EcrecoverUsage(AbstractDetector):
    ARGUMENT = 'detect-ecrecover'
    HELP = 'Detects usage of the ecrecover function in smart contract functions.'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH
    WIKI = "https://docs.hedera.com/hedera/core-concepts/keys-and-signatures"
    WIKI_TITLE = "Usage of ecrecover"
    WIKI_DESCRIPTION = "The ecrecover function is used to extract an Ethereum address from a signature."
    WIKI_RECOMMENDATION = "Ensure the parameters and return value of ecrecover are securely handled to prevent misuse or attacks. HEDERA supports Ed25519 keys, while ecrecover always expects ECDSA!"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract ExampleContract {
    function verifySignature(bytes32 hash, uint8 v, bytes32 r, bytes32 s) public pure returns (address) {
        return ecrecover(hash, v, r, s);
    }
}
```
"""
    def _detect(self):
        results = []
        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions:
                for node in function.nodes:
                    for ir in node.irs:
                        if isinstance(ir, SolidityCall) and isinstance(ir.function, SolidityFunction) and ir.function.name[0:9] == 'ecrecover':
                            info = {
                                'description': f'The function `{function.name}` in contract `{contract.name}` uses `ecrecover`.',
                                'contract': contract.name,
                                'function_name': function.name,
                                'location': node.source_mapping
                            }
                            info = [f"ecrecover function call detected\n"]
                            result = self.generate_result(info)
                            results.append(result)
        return results
