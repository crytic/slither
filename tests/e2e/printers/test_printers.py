import itertools
import re
from collections import Counter
from fnmatch import fnmatch
from pathlib import Path
from typing import List, Tuple, Type
import pytest

from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson
from crytic_compile.utils.zip import load_from_zip

from slither import Slither
from slither.printers.inheritance.inheritance_graph import PrinterInheritanceGraph
from slither.printers import all_printers
from slither.printers.abstract_printer import AbstractPrinter


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"

PRINTER_DATA_DIR = Path(__file__).resolve().parent.parent / "solc_parsing" / "test_data" / "compile"


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


known_failures = {
    all_printers.Halstead: [
        "top_level_variable-0.8.0.sol-0.8.12-compact.zip",
        "top_level_variable2-0.8.0.sol-0.8.12-compact.zip",
        "custom_error_with_state_variable.sol-0.8.12-compact.zip",
    ],
    all_printers.PrinterSlithIRSSA: [
        "*",
    ],
}


def generate_all_tests() -> List[Tuple[Path, Type[AbstractPrinter]]]:
    """Generates tests cases for all printers."""
    printers = []
    for printer_name in dir(all_printers):
        obj = getattr(all_printers, printer_name)
        if (
            isinstance(obj, type)
            and issubclass(obj, AbstractPrinter)
            and printer_name != "PrinterEVM"
        ):
            printers.append(obj)

    tests = []
    for version in ["*0.5.17-compact.zip", "*0.8.12-compact.zip"]:
        for test_file, printer in itertools.product(PRINTER_DATA_DIR.glob(version), printers):

            known_errors = known_failures.get(printer, [])
            if not any(fnmatch(test_file.name, pattern) for pattern in known_errors):
                tests.append((test_file, printer))

    # TODO(dm) Handle the EVM CFG Builder printer
    # cd ../../.. || exit
    # # Needed for evm printer
    # pip install evm-cfg-builder
    # solc-select use "0.5.1"
    # if ! slither examples/scripts/test_evm_api.sol --print evm; then
    #     echo "EVM printer failed"
    # fi

    return tests


ALL_TESTS = generate_all_tests()


def id_test(test_item: Tuple[Path, Type[AbstractPrinter]]) -> str:
    """Returns the ID of the test."""
    return f"{test_item[0].name}-{test_item[1].ARGUMENT}"


@pytest.mark.parametrize("test_item", ALL_TESTS, ids=id_test)
def test_printer(test_item: Tuple[Path, Type[AbstractPrinter]], snapshot):

    test_file, printer = test_item

    crytic_compile = load_from_zip(test_file.as_posix())[0]

    sl = Slither(crytic_compile)
    sl.register_printer(printer)

    results = sl.run_printers()

    actual_output = ""
    for printer_results in results:
        actual_output += f"{printer_results['description']}\n"

        # Some printers also create files, so lets compare their output too
        for element in printer_results["elements"]:
            if element["type"] == "file":
                actual_output += f"{element['name']['content']}\n"

                try:
                    Path(element["name"]["filename"]).unlink()
                except FileNotFoundError:
                    pass

    assert snapshot() == actual_output
