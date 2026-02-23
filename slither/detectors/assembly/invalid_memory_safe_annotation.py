"""
Detector for incorrect memory-safe-assembly annotations.

Solidity's `@solidity memory-safe-assembly` annotation only works in NatSpec
comments (/// or /** */), not in regular comments (// or /* */).
"""

import re

from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output

# Correct annotation text
_CORRECT_ANNOTATION = "memory-safe-assembly"

# Pattern for regular (non-NatSpec) single-line comment with the annotation
_REGULAR_SINGLE = re.compile(r"^\s*//(?!/)\s*@solidity\s+memory-safe-assembly")

# Pattern for regular (non-NatSpec) multi-line comment with the annotation
_REGULAR_MULTI = re.compile(r"^\s*/\*(?!\*)\s*@solidity\s+memory-safe-assembly")

# Common misspellings / typo patterns in NatSpec comments
_NATSPEC_TYPO = re.compile(
    r"^\s*(?:///|/\*\*)\s*@solidity\s+"
    r"(?:memory-safe-assembl[^y]"  # e.g. memory-safe-assembla
    r"|memory-sage-assembly"  # sage instead of safe
    r"|memory safe assembly"  # missing hyphens
    r"|memory-safe assembly"  # missing second hyphen
    r"|memory safe-assembly"  # missing first hyphen
    r"|memoery-safe-assembly"  # typo in memory
    r"|memroy-safe-assembly"  # typo in memory
    r")"
)


class InvalidMemorySafeAnnotation(AbstractDetector):
    """
    Detect incorrect usage of the @solidity memory-safe-assembly annotation.
    """

    ARGUMENT = "incorrect-memory-safe-assembly"
    HELP = "Incorrect memory-safe-assembly annotation"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-memory-safe-assembly"

    WIKI_TITLE = "Incorrect memory-safe-assembly annotation"
    WIKI_DESCRIPTION = (
        "The `@solidity memory-safe-assembly` annotation only works in NatSpec comments "
        "(`///` or `/** */`). Using it in regular comments (`//` or `/* */`) is silently "
        "ignored by the compiler, and the expected memory optimizations will not be applied."
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract C {
    function f() external pure returns (uint256 result) {
        // @solidity memory-safe-assembly
        assembly {
            result := 42
        }
    }
}
```
The annotation uses a regular comment (`//`) instead of NatSpec (`///`), \
so the compiler ignores it and does not apply memory optimizations."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "Use NatSpec comments for the annotation: "
        "`/// @solidity memory-safe-assembly` or `/** @solidity memory-safe-assembly */`."
    )

    LANGUAGE = "solidity"

    def _detect(self) -> list[Output]:
        results = []

        for contract in self.compilation_unit.contracts_derived:
            if contract.is_interface or contract.is_from_dependency():
                continue

            for function in contract.functions_and_modifiers_declared:
                if not function.contains_assembly:
                    continue
                if not function.source_mapping:
                    continue

                filename = function.source_mapping.filename.absolute
                source_code = self.compilation_unit.core.source_code.get(filename)
                if not source_code:
                    continue

                source_lines = source_code.splitlines()
                func_lines = function.source_mapping.lines

                for line_num in func_lines:
                    if line_num < 1 or line_num > len(source_lines):
                        continue

                    line_text = source_lines[line_num - 1]

                    # Check for regular comment with correct annotation text
                    if _REGULAR_SINGLE.search(line_text):
                        info: DETECTOR_INFO = [
                            function,
                            f" uses a regular comment for memory-safe-assembly annotation (line {line_num}). "
                            "Use `///` (NatSpec) instead of `//`.\n",
                        ]
                        results.append(self.generate_result(info))

                    elif _REGULAR_MULTI.search(line_text):
                        info = [
                            function,
                            f" uses a regular comment for memory-safe-assembly annotation (line {line_num}). "
                            "Use `/** */` (NatSpec) instead of `/* */`.\n",
                        ]
                        results.append(self.generate_result(info))

                    elif _NATSPEC_TYPO.search(line_text):
                        info = [
                            function,
                            f" has a misspelled memory-safe-assembly annotation (line {line_num}). "
                            "Use `/// @solidity memory-safe-assembly` with exact spelling.\n",
                        ]
                        results.append(self.generate_result(info))

        return results
