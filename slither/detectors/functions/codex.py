import logging
import os
from typing import List

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output

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

    def _detect(self) -> List[Output]:
        results: List[Output] = []

        if not self.slither.codex_enabled:
            return []

        try:
            # pylint: disable=import-outside-toplevel
            import openai
        except ImportError:
            logging.info("OpenAI was not installed")
            logging.info('run "pip install openai"')
            return []

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            logging.info(
                "Please provide an Open API Key in OPENAI_API_KEY (https://beta.openai.com/account/api-keys)"
            )
            return []
        openai.api_key = api_key

        for contract in self.compilation_unit.contracts:
            if self.slither.codex_contracts != "all" and contract.name not in self.slither.codex_contracts.split(","):
                continue
            prompt = "Analyze this Solidity contract and find the vulnerabilities. If you find any vulnerabilities, begin the response with {}".format(VULN_FOUND)
            src_mapping = contract.source_mapping
            content = contract.compilation_unit.core.source_code[src_mapping.filename.absolute]
            start = src_mapping.start
            end = src_mapping.start + src_mapping.length
            prompt += content[start:end]
            logging.info("Querying OpenAI")
            print("Querying OpenAI")
            answer = ""
            res = {}
            try:
                res = openai.Completion.create(  # type: ignore
                    prompt=prompt,
                    model=self.slither.codex_model,
                    temperature=self.slither.codex_temperature,
                    max_tokens=self.slither.codex_max_tokens,
                )
            except Exception as e:
                print("OpenAI request failed: " + str(e))
                logging.info("OpenAI request failed: " + str(e))

            """ OpenAI completion response shape example:
            {
                "choices": [
                    {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": null,
                    "text": "VULNERABILITIES:. The withdraw() function does not check..."
                    }
                ],
                "created": 1670357537,
                "id": "cmpl-6KYaXdA6QIisHlTMM7RCJ1nR5wTKx",
                "model": "text-davinci-003",
                "object": "text_completion",
                "usage": {
                    "completion_tokens": 80,
                    "prompt_tokens": 249,
                    "total_tokens": 329
                }
            } """

            if len(res.get("choices", [])) and VULN_FOUND in res["choices"][0].get("text", ""):
                # remove VULN_FOUND keyword and cleanup
                answer = res["choices"][0]["text"].replace(VULN_FOUND, "").replace("\n", "").replace(": ", "")

            if len(answer):
                info = [
                    "Codex detected a potential bug in ",
                    contract,
                    "\n",
                    answer,
                    "\n",
                ]

                res = self.generate_result(info)
                results.append(res)
        return results
