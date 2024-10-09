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
from slither.printers.summary.slithir import PrinterSlithIR


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
    # Let also test the include/exclude interface behavior
    # Check that the interface is not included
    assert "MyInterfaceX" not in content

    slither.include_interfaces = True
    output = printer.output("test_printer.dot")
    content = output.elements[0]["name"]["content"]
    assert "MyInterfaceX" in content

    # Remove test generated files
    Path("test_printer.dot").unlink(missing_ok=True)


@pytest.mark.skipif(
    not foundry_available or not project_ready, reason="requires Foundry and project setup"
)
def test_printer_cheatcode():
    slither = Slither(
        Path(TEST_DATA_DIR, "test_printer_cheatcode").as_posix(), foundry_compile_all=True
    )

    printer = CheatcodePrinter(slither=slither, logger=None)
    output = printer.output("")

    assert (
        output.data["description"]
        == "CounterTest (test/Counter.t.sol)\n\tsetUp\n\t\tdeal - (test/Counter.t.sol#21 (9 - 32)\n\t\tvm.deal(alice,1000000000000000000)\n\n\t\tdeal - (test/Counter.t.sol#22 (9 - 30)\n\t\tvm.deal(bob,2000000000000000000)\n\n\ttestIncrement\n\t\tprank - (test/Counter.t.sol#28 (9 - 24)\n\t\tvm.prank(alice)\n\n\t\tassertEq - (test/Counter.t.sol#30 (9 - 38)\n\t\tassertEq(counter.number(),1)\n\n\t\tprank - (test/Counter.t.sol#32 (9 - 22)\n\t\tvm.prank(bob)\n\n\t\tassertEq - (test/Counter.t.sol#34 (9 - 38)\n\t\tassertEq(counter.number(),2)\n\n"
    )


def test_slithir_printer(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    standard_json = SolcStandardJson()
    standard_json.add_source_file(
        Path(TEST_DATA_DIR, "test_printer_slithir", "bug-2266.sol").as_posix()
    )
    compilation = CryticCompile(standard_json, solc=solc_path)
    slither = Slither(compilation)

    printer = PrinterSlithIR(slither, logger=None)
    output = printer.output("test_printer_slithir.dot")

    assert "slither.core.solidity_types" not in output.data["description"]
