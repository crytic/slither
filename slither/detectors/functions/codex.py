import logging
import os
from typing import List

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output

logger = logging.getLogger("Slither")


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
            prompt = "Is there a vulnerability in this solidity contracts?\n"
            src_mapping = contract.source_mapping
            content = contract.compilation_unit.core.source_code[src_mapping.filename.absolute]
            start = src_mapping.start
            end = src_mapping.start + src_mapping.length
            prompt += content[start:end]
            answer = openai.Completion.create(  # type: ignore
                model="text-davinci-003", prompt=prompt, temperature=0, max_tokens=200
            )

            if "choices" in answer:
                if answer["choices"]:
                    if "text" in answer["choices"][0]:
                        if "Yes," in answer["choices"][0]["text"]:
                            info = [
                                "Codex detected a potential bug in ",
                                contract,
                                "\n",
                                answer["choices"][0]["text"],
                                "\n",
                            ]

                            res = self.generate_result(info)
                            results.append(res)

        return results
