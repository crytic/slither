"""
Claude-based vulnerability detector for Slither
Supports both Anthropic API and Claude Code CLI (for MAX subscribers)
"""
import logging
import uuid
from typing import List, Union

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils import claude
from slither.utils.output import Output, SupportedOutput

logger = logging.getLogger("Slither")

VULN_FOUND = "VULNERABILITY_DETECTED"


class Claude(AbstractDetector):
    """
    Use Claude to detect vulnerabilities in smart contracts
    """

    ARGUMENT = "claude"
    HELP = "Use Claude to find vulnerabilities."
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.LOW

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#claude"

    WIKI_TITLE = "Claude"
    WIKI_DESCRIPTION = "Use [Claude](https://www.anthropic.com/claude) to find vulnerabilities"

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """N/A"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Review Claude's analysis and recommendations."

    def _run_claude(self, logging_file: str, prompt: str) -> str:
        """
        Handle the Claude logic - supports both API and Claude Code CLI

        Args:
            logging_file (str): file where to log the queries
            prompt (str): prompt to send to Claude

        Returns:
            Claude answer (str)
        """
        if self.slither.claude_log:
            claude.log_claude(logging_file, f"Model: {self.slither.claude_model}")
            claude.log_claude(logging_file, "Q: " + prompt)

        answer = ""

        # Try Claude Code CLI first if enabled (no API cost for MAX subscribers)
        if self.slither.claude_use_code:
            if claude.check_claude_code_available():
                response = claude.run_claude_code(prompt, model=self.slither.claude_model)
                if response:
                    if self.slither.claude_log:
                        claude.log_claude(logging_file, "A: " + response)
                    if VULN_FOUND in response:
                        answer = response.replace(VULN_FOUND, "").strip()
                    return answer
            else:
                logger.info(
                    "Claude Code not available. Set CLAUDE_CODE_OAUTH_TOKEN or install Claude Code CLI"
                )
                return ""

        # Fall back to API
        client = claude.get_claude_client()
        if client is None:
            return ""

        response = claude.run_claude_api(
            client,
            prompt,
            model=self.slither.claude_model,
            max_tokens=self.slither.claude_max_tokens,
        )

        if response:
            if self.slither.claude_log:
                claude.log_claude(logging_file, "A: " + response)
            if VULN_FOUND in response:
                answer = response.replace(VULN_FOUND, "").strip()
        else:
            if self.slither.claude_log:
                claude.log_claude(logging_file, "A: Claude request failed")

        return answer

    def _detect(self) -> List[Output]:
        results: List[Output] = []

        if not self.slither.claude_enabled:
            return []

        logging_file = str(uuid.uuid4())

        # Filter contracts to analyze
        contracts_to_analyze = []
        for contract in self.compilation_unit.contracts:
            if (
                self.slither.claude_contracts != "all"
                and contract.name not in self.slither.claude_contracts.split(",")
            ):
                continue
            contracts_to_analyze.append(contract)

        total = len(contracts_to_analyze)
        logger.info(f"Claude: Using model '{self.slither.claude_model}'")
        logger.info(f"Claude: Analyzing {total} contract(s)...")

        for idx, contract in enumerate(contracts_to_analyze, 1):
            logger.info(f"Claude: [{idx}/{total}] Analyzing {contract.name}...")

            prompt = self._build_prompt(contract.source_mapping.content)
            answer = self._run_claude(logging_file, prompt)

            if answer:
                logger.info(
                    f"Claude: [{idx}/{total}] Found potential vulnerability in {contract.name}"
                )
            else:
                logger.info(f"Claude: [{idx}/{total}] No issues found in {contract.name}")

            if answer:
                info: List[Union[str, SupportedOutput]] = [
                    "Claude detected a potential vulnerability in ",
                    contract,
                    "\n",
                    answer,
                    "\n",
                ]

                new_result = self.generate_result(info)
                results.append(new_result)

        return results

    def _build_prompt(self, source_code: str) -> str:
        """
        Build the prompt for Claude analysis

        Args:
            source_code: The Solidity source code to analyze

        Returns:
            The formatted prompt
        """
        return f"""You are a smart contract security expert. Analyze the following Solidity contract for security vulnerabilities.

Focus on:
1. Reentrancy vulnerabilities
2. Access control issues
3. Integer overflow/underflow (for Solidity < 0.8.0)
4. Unchecked external calls
5. Front-running vulnerabilities
6. Logic errors
7. Gas optimization issues that could lead to DoS
8. Signature replay attacks
9. Oracle manipulation
10. Flash loan attack vectors

If you find any vulnerabilities, begin your response with "{VULN_FOUND}" followed by a detailed explanation of each vulnerability, its severity (Critical/High/Medium/Low), and recommended fixes.

If no vulnerabilities are found, respond with "No vulnerabilities detected."

Contract source code:
```solidity
{source_code}
```

Analyze this contract thoroughly and provide your security assessment:"""
