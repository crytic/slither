from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output
from slither.core.declarations import Contract, Function
import re

class HardcodedNigerianSecrets(AbstractDetector):
    """
    Detects hardcoded Nigerian fintech keys and crypto wallet seeds in Solidity contracts.
    """
    ARGUMENT = "hardcoded-nigerian-secrets"
    HELP = "Hardcoded Nigerian fintech and crypto secrets detected"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#hardcoded-nigerian-secrets"
    WIKI_TITLE = "Hardcoded Nigerian Secrets"
    WIKI_DESCRIPTION = "Hardcoding Nigerian payment keys or wallet seeds in contracts exposes them to theft. Use secure storage instead."
    WIKI_EXPLOIT_SCENARIO = "Attacker decompiles contract and extracts Paystack key for unauthorized transactions."
    WIKI_RECOMMENDATION = "Use environment variables, oracles, or secure vaults for secrets."

    PATTERNS = [
        (r'sk_(live|test)_[a-z0-9]{50,}', "Paystack Secret Key", 3.5),
        (r'flwseck[_-]?[a-z0-9]{30,}', "Flutterwave Secret Key", 3.0),
        (r'\d{10,15}\|[a-z0-9]{40,}', "Remita Merchant ID + Hash", 3.0),
        (r'mackey["\']?\s*[:=]\s*["\']?[0-9a-f]{64}["\']?', "Interswitch MAC Key", 3.5),
        (r'(?:^|\s)([a-z]+(?: [a-z]+){11,23})(?:\s|$)', "12-24 Word Wallet Seed Phrase", 4.0),
    ]

    def _check_entropy(self, match: str, min_entropy: float) -> bool:
        from math import log2
        unique_chars = len(set(match))
        if unique_chars == 0:
            return False
        entropy = log2(unique_chars) * len(match) / unique_chars
        return entropy >= min_entropy

    def _detect(self):
        results = []
        for contract in self.compilation_unit.contracts_derived:
            for func in contract.functions:
                for node in func.nodes:
                    if node.source_mapping.content:
                        src = node.source_mapping.content
                        for pattern, name, min_entropy in self.PATTERNS:
                            matches = re.finditer(pattern, src, re.IGNORECASE)
                            for match in matches:
                                secret = match.group(0)
                                if self._check_entropy(secret, min_entropy):
                                    info = [f"{name} detected in ", func, " (", node, ")\n"]
                                    res = self.generate_result(info)
                                    results.append(res)
        return results
