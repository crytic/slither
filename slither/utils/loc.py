from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

from slither import Slither
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.tests_pattern import is_test_file


@dataclass
class LoCInfo:
    loc: int = 0
    sloc: int = 0
    cloc: int = 0

    def total(self) -> int:
        return self.loc + self.sloc + self.cloc


@dataclass
class LoC:
    src: LoCInfo = field(default_factory=LoCInfo)
    dep: LoCInfo = field(default_factory=LoCInfo)
    test: LoCInfo = field(default_factory=LoCInfo)

    def to_pretty_table(self) -> MyPrettyTable:
        table = MyPrettyTable(["", "src", "dep", "test"])

        table.add_row(["loc", str(self.src.loc), str(self.dep.loc), str(self.test.loc)])
        table.add_row(["sloc", str(self.src.sloc), str(self.dep.sloc), str(self.test.sloc)])
        table.add_row(["cloc", str(self.src.cloc), str(self.dep.cloc), str(self.test.cloc)])
        table.add_row(
            ["Total", str(self.src.total()), str(self.dep.total()), str(self.test.total())]
        )
        return table


def count_lines(contract_lines: List[str]) -> Tuple[int, int, int]:
    """Function to count and classify the lines of code in a contract.
    Args:
        contract_lines: list(str) representing the lines of a contract.
    Returns:
        tuple(int, int, int) representing (cloc, sloc, loc)
    """
    multiline_comment = False
    cloc = 0
    sloc = 0
    loc = 0

    for line in contract_lines:
        loc += 1
        stripped_line = line.strip()
        if not multiline_comment:
            if stripped_line.startswith("//"):
                cloc += 1
            elif "/*" in stripped_line:
                # Account for case where /* is followed by */ on the same line.
                # If it is, then multiline_comment does not need to be set to True
                start_idx = stripped_line.find("/*")
                end_idx = stripped_line.find("*/", start_idx + 2)
                if end_idx == -1:
                    multiline_comment = True
                cloc += 1
            elif stripped_line:
                sloc += 1
        else:
            cloc += 1
            if "*/" in stripped_line:
                multiline_comment = False

    return cloc, sloc, loc


def _update_lines(loc_info: LoCInfo, lines: list) -> None:
    """An internal function used to update (mutate in place) the loc_info.

    Args:
        loc_info: LoCInfo to be updated
        lines: list(str) representing the lines of a contract.
    """
    cloc, sloc, loc = count_lines(lines)
    loc_info.loc += loc
    loc_info.cloc += cloc
    loc_info.sloc += sloc


def compute_loc_metrics(slither: Slither) -> LoC:
    """Used to compute the lines of code metrics for a Slither object.

    Args:
        slither: A Slither object
    Returns:
        A LoC object
    """

    loc = LoC()

    for filename, source_code in slither.source_code.items():
        current_lines = source_code.splitlines()
        is_dep = False
        if slither.crytic_compile:
            is_dep = slither.crytic_compile.is_dependency(filename)
        loc_type = loc.dep if is_dep else loc.test if is_test_file(Path(filename)) else loc.src
        _update_lines(loc_type, current_lines)
    return loc
