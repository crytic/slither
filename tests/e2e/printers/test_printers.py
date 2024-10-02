import re
from collections import Counter
from pathlib import Path

from crytic_compile import CryticCompile, compile_all
from crytic_compile.platform.solc_standard_json import SolcStandardJson

from slither import Slither
from slither.printers.inheritance.inheritance_graph import PrinterInheritanceGraph
from slither.printers.summary.external_calls import ExternalCallPrinter


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


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


def test_external_call_printers(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    compilation = compile_all(
        (TEST_DATA_DIR / "test_external_calls" / "A.sol").as_posix(), solc=solc_path
    ).pop()
    slither = Slither(compilation)

    printer = ExternalCallPrinter(slither, None)
    output = printer.output("")

    # The test is not great here, but they will soon be moved to a snapshot based system
    assert output is not None
