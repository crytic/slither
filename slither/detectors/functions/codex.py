import logging
import uuid
from typing import List, Union

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils import codex
from slither.utils.output import Output, SupportedOutput

logger = logging.getLogger("Slither")

VULN_FOUND = "VULN_FOUND"


class Codex(AbstractDetector):
    """
    Use codex to detect vulnerability
    """

    ARGUMENT = "codex"
    HELP = "Use Codex to find vulnerabilities."
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.LOW

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#codex"

    WIKI_TITLE = "Codex"
    WIKI_DESCRIPTION = "Use [codex](https://openai.com/blog/openai-codex/) to find vulnerabilities"

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """N/A"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Review codex's message."

    def _run_codex(self, logging_file: str, prompt: str) -> str:
        """
        Handle the codex logic

        Args:
            logging_file (str): file where to log the queries
            prompt (str): prompt to send to codex

        Returns:
            codex answer (str)
        """
        openai_module = codex.openai_module()  # type: ignore
        if openai_module is None:
            return ""

        if self.slither.codex_log:
            codex.log_codex(logging_file, "Q: " + prompt)

        answer = ""
        res = {}

        if self.slither.codex_organization:
            openai_module.organization = self.slither.codex_organization

        try:
            res = openai_module.Completion.create(
                prompt=prompt,
                model=self.slither.codex_model,
                temperature=self.slither.codex_temperature,
                max_tokens=self.slither.codex_max_tokens,
            )
        except Exception as e:  # pylint: disable=broad-except
            logger.info("OpenAI request failed: " + str(e))

        # """ OpenAI completion response shape example:
        # {
        #     "choices": [
        #         {
        #         "finish_reason": "stop",
        #         "index": 0,
        #         "logprobs": null,
        #         "text": "VULNERABILITIES:. The withdraw() function does not check..."
        #         }
        #     ],
        #     "created": 1670357537,
        #     "id": "cmpl-6KYaXdA6QIisHlTMM7RCJ1nR5wTKx",
        #     "model": "text-davinci-003",
        #     "object": "text_completion",
        #     "usage": {
        #         "completion_tokens": 80,
        #         "prompt_tokens": 249,
        #         "total_tokens": 329
        #     }
        # } """

        if res:
            if self.slither.codex_log:
                codex.log_codex(logging_file, "A: " + str(res))
        else:
            codex.log_codex(logging_file, "A: Codex failed")

        if res.get("choices", []) and VULN_FOUND in res["choices"][0].get("text", ""):
            # remove VULN_FOUND keyword and cleanup
            answer = (
                res["choices"][0]["text"]
                .replace(VULN_FOUND, "")
                .replace("\n", "")
                .replace(": ", "")
            )
        return answer

    def _detect(self) -> List[Output]:
        results: List[Output] = []

        if not self.slither.codex_enabled:
            return []

        logging_file = str(uuid.uuid4())

        for contract in self.compilation_unit.contracts:
            if (
                self.slither.codex_contracts != "all"
                and contract.name not in self.slither.codex_contracts.split(",")
            ):
                continue
            prompt = f"Analyze this Solidity contract and find the vulnerabilities. If you find any vulnerabilities, begin the response with {VULN_FOUND}\n"
            prompt += contract.source_mapping.content

            answer = self._run_codex(logging_file, prompt)

            if answer:
                info: List[Union[str, SupportedOutput]] = [
                    "Codex detected a potential bug in ",
                    contract,
                    "\n",
                    answer,
                    "\n",
                ]

                new_result = self.generate_result(info)
                results.append(new_result)
        return results
