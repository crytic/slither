"""
Detector for invalid memory-safe assembly annotations.

Detects:
1. @solidity memory-safe-assembly in regular comments (// or /* */) instead of NatSpec (/// or /** */)
2. Typos in the annotation
3. Annotation not immediately before assembly block
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.core.cfg.node import NodeType
from slither.utils.output import Output

if TYPE_CHECKING:
    from slither.core.declarations import Function


class InvalidMemorySafeAssembly(AbstractDetector):
    """
    Detect invalid memory-safe assembly annotations
    """

    ARGUMENT = "incorrect-memory-safe"
    HELP = "Incorrect memory-safe assembly annotation"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-memory-safe-assembly-annotation"

    WIKI_TITLE = "Incorrect memory-safe assembly annotation"
    WIKI_DESCRIPTION = """Detects incorrect usage of the `@solidity memory-safe-assembly` annotation:
- Using regular comments (`//` or `/* */`) instead of NatSpec comments (`///` or `/** */`)
- Typos in the annotation text
- Annotation not immediately preceding the assembly block

The `@solidity memory-safe-assembly` annotation only works in NatSpec comments. Using it in regular comments has no effect, and the compiler will not apply memory optimizations."""

    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Example {
    function bad() external pure returns (bytes32 result) {
        // @solidity memory-safe-assembly
        assembly {
            result := mload(0x40)
        }
    }
}
```
The annotation is in a regular comment (`//`) instead of a NatSpec comment (`///`), so the compiler ignores it and won't apply memory optimizations."""

    WIKI_RECOMMENDATION = """Use NatSpec comments for the memory-safe assembly annotation:
```solidity
/// @solidity memory-safe-assembly
assembly {
    // ...
}
```
Or using multi-line NatSpec:
```solidity
/** @solidity memory-safe-assembly */
assembly {
    // ...
}
```"""

    # Patterns to detect
    CORRECT_ANNOTATION = "memory-safe-assembly"

    # Common typos and variations
    TYPO_PATTERNS = [
        (r"memory-sage-assembly", "memory-sage-assembly (typo: 'sage' instead of 'safe')"),
        (r"memory\s+safe\s+assembly", "memory safe assembly (missing hyphens)"),
        (r"memory_safe_assembly", "memory_safe_assembly (underscores instead of hyphens)"),
        (r"memorysafe-assembly", "memorysafe-assembly (missing hyphen after 'memory')"),
        (r"memory-safeassembly", "memory-safeassembly (missing hyphen after 'safe')"),
        (r"memory-safe-assemby", "memory-safe-assemby (typo: 'assemby')"),
        (r"memory-safe-asembly", "memory-safe-asembly (typo: 'asembly')"),
        (r"memmory-safe-assembly", "memmory-safe-assembly (typo: 'memmory')"),
    ]

    def _get_source_lines(self, filename: str) -> list[str]:
        """Get source code lines for a file."""
        if filename not in self.slither.source_code:
            return []
        return self.slither.source_code[filename].splitlines()

    def _check_for_annotation_issues(
        self, lines: list[str], asm_line_num: int, filename: str
    ) -> list[tuple[str, int, str]]:
        """
        Check lines before assembly block for annotation issues.

        Returns list of (issue_type, line_number, description) tuples.
        """
        issues: list[tuple[str, int, str]] = []

        # Look at up to 10 lines before the assembly block
        start_check = max(0, asm_line_num - 10)
        found_annotation = False
        annotation_line_num = -1
        lines_between = 0

        for i in range(asm_line_num - 1, start_check - 1, -1):
            if i < 0 or i >= len(lines):
                continue

            line = lines[i].strip()

            # Skip empty lines when counting distance
            if not line:
                if found_annotation:
                    lines_between += 1
                continue

            # Check for @solidity annotation in any comment
            has_solidity_annotation = "@solidity" in line.lower()

            if has_solidity_annotation:
                found_annotation = True
                annotation_line_num = i + 1  # 1-indexed

                # Check if it's in a regular comment (bad) vs NatSpec (good)
                is_regular_single = line.startswith("//") and not line.startswith("///")
                is_regular_multi = line.startswith("/*") and not line.startswith("/**")

                if is_regular_single or is_regular_multi:
                    issues.append(
                        (
                            "regular_comment",
                            annotation_line_num,
                            f"Memory-safe annotation in regular comment will be ignored. "
                            f"Use NatSpec comment (/// or /** */) instead of ({line[:3]}...)",
                        )
                    )

                # Check for typos in the annotation
                for pattern, description in self.TYPO_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(
                            (
                                "typo",
                                annotation_line_num,
                                f"Typo in memory-safe annotation: {description}",
                            )
                        )
                        break

                # Check if correct annotation text is present (even in NatSpec)
                if self.CORRECT_ANNOTATION not in line.lower():
                    # Only flag if we found @solidity but not the correct full annotation
                    # and we didn't already flag a typo
                    if not any(issue[0] == "typo" for issue in issues):
                        issues.append(
                            (
                                "invalid_annotation",
                                annotation_line_num,
                                "Invalid @solidity annotation format. Expected '@solidity memory-safe-assembly'",
                            )
                        )

                break  # Stop after finding the first annotation

            # If we find a non-empty, non-comment line, stop searching
            if not line.startswith("//") and not line.startswith("/*") and not line.startswith("*"):
                if found_annotation:
                    # There's code between annotation and assembly
                    issues.append(
                        (
                            "not_adjacent",
                            annotation_line_num,
                            f"Memory-safe annotation is not immediately before assembly block "
                            f"(found {lines_between} non-empty lines between)",
                        )
                    )
                break

            if found_annotation:
                lines_between += 1

        return issues

    def _check_function(self, function: Function) -> list[Output]:
        """Check a function for invalid memory-safe assembly annotations."""
        results: list[Output] = []

        for node in function.nodes:
            if node.type != NodeType.ASSEMBLY:
                continue

            # Get source mapping info
            if not node.source_mapping or not node.source_mapping.lines:
                continue

            filename = node.source_mapping.filename.absolute
            asm_line_num = node.source_mapping.lines[0]  # 1-indexed

            # Get source lines
            source_lines = self._get_source_lines(filename)
            if not source_lines:
                continue

            # Check for issues (convert to 0-indexed for array access)
            issues = self._check_for_annotation_issues(source_lines, asm_line_num - 1, filename)

            for issue_type, line_num, description in issues:
                info: DETECTOR_INFO = [
                    function,
                    " contains an invalid memory-safe assembly annotation:\n",
                    f"\t- {description}\n",
                    f"\t- Location: line {line_num}\n",
                    "\t- Assembly block: ",
                    node,
                    "\n",
                ]
                result = self.generate_result(info)
                results.append(result)

        return results

    def _detect(self) -> list[Output]:
        results: list[Output] = []

        for contract in self.contracts:
            for function in contract.functions_and_modifiers_declared:
                if function.contract_declarer != contract:
                    continue

                if function.contains_assembly:
                    results.extend(self._check_function(function))

        return results
