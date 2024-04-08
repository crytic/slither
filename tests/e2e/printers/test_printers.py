import re
import shutil
from collections import Counter
from pathlib import Path
import pytest

from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson

from slither import Slither
from slither.printers.inheritance.inheritance_graph import PrinterInheritanceGraph
from slither.printers.summary.cheatcodes import CheatcodePrinter


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"

foundry_available = shutil.which("forge") is not None
project_ready = Path(TEST_DATA_DIR, "test_printer_cheatcode/lib/forge-std").exists()


def test_inheritance_printer(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    standard_json = SolcStandardJson()
    standard_json.add_source_file(Path(TEST_DATA_DIR, "test_contract_names", "A.sol").as_posix())
    standard_json.add_source_file(Path(TEST_DATA_DIR, "test_contract_names", "B.sol").as_posix())
    standard_json.add_source_file(Path(TEST_DATA_DIR, "test_contract_names", "B2.sol").as_posix())
    standard_json.add_source_file(Path(TEST_DATA_DIR, "test_contract_names", "C.sol").as_posix())
    compilation = CryticCompile(standard_json, solc=solc_path)
    slither = Slither(compilation)
    printer = PrinterInheritanceGraph(slither=slither, logger=None)

    output = printer.output("test_printer.dot")
    content = output.elements[0]["name"]["content"]

    pattern = re.compile(r"(?:c\d+_)?(\w+ -> )(?:c\d+_)(\w+)")
    matches = re.findall(pattern, content)
    relations = ["".join(m) for m in matches]

    counter = Counter(relations)

    assert counter["B -> A"] == 2
    assert counter["C -> A"] == 1


@pytest.mark.skipif(
    not foundry_available or not project_ready, reason="requires Foundry and project setup"
)
def test_printer_cheatcode():
    slither = Slither(
        Path(TEST_DATA_DIR, "test_printer_cheatcode").as_posix(), foundry_compile_all=True
    )

    printer = CheatcodePrinter(slither=slither, logger=None)
    output = printer.output("cheatcode.out")

    assert (
        output
        == "CounterTest (test/Counter.t.sol)\n\tsetUp\n\t\tL[21]: deal\n\t\tL[22]: deal\n\ttestIncrement\n\t\tL[28]: prank\n\t\tL[30]: assertEq\n\t\tL[32]: prank\n\t\tL[34]: assertEq\n"
    )
