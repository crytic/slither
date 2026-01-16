from argparse import Namespace
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Set, Union, OrderedDict
import re

import pytest

from slither import Slither
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.output import Output
from slither.core.filtering import FilteringRule, FilteringAction
from slither.__main__ import parse_filter_paths

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


foundry_available = shutil.which("forge") is not None
project_ready = Path(TEST_DATA_DIR, "test_filtering/lib/forge-std").exists()


class DummyPrinter(AbstractPrinter):
    ARGUMENT = "dummy_printer"
    HELP = ".."
    WIKI = ".."

    def output(self, _: str) -> Output:
        output = []
        for contract in self.contracts:
            for function in contract.functions:
                output.append(f"{function.contract_declarer.name}.{function.name}")

        output = self.generate_output(",".join(output))
        return output

    @staticmethod
    def analyze_dummy_output(output: OrderedDict) -> Set[str]:
        return set(output["description"].split(","))


class DummyDetector(AbstractDetector):
    ARGUMENT = "dummy_detector"  # run the detector with slither.py --ARGUMENT
    HELP = ".."  # help information
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.LOW

    WIKI = ".."

    WIKI_TITLE = ".."
    WIKI_DESCRIPTION = ".."
    WIKI_EXPLOIT_SCENARIO = ".."
    WIKI_RECOMMENDATION = ".."

    def _detect(self) -> List[Output]:
        results = []
        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions:
                results.append(self.generate_result([function]))

        return results

    @staticmethod
    def analyze_dummy_output(results: Dict) -> Set[str]:
        output = set()
        for result in results:
            for element in result.get("elements", []):
                assert element.get("type") == "function"
                contract = element.get("type_specific_fields", {}).get("parent", {}).get("name")
                output.add(f"{contract}.{element['name']}")

        return output


@pytest.mark.skipif(
    not foundry_available or not project_ready, reason="requires Foundry and project setup"
)
def test_filtering():
    def run_detector_for_filtering(
        sl: Slither,
        filtering: Union[List[FilteringRule], None],
        default_action: FilteringAction,
    ):
        # First, reset any results
        # pylint: disable=protected-access
        sl._currently_seen_resuts = set()

        # Set up default action
        sl.default_action = default_action

        if filtering is not None:
            sl.filters = filtering

        return DummyDetector.analyze_dummy_output(sl.run_detectors().pop())

    slither = Slither(Path(TEST_DATA_DIR, "test_filtering").as_posix())
    slither.register_detector(DummyDetector)

    # First, check that if we deny everything, we don't run on anything
    output = run_detector_for_filtering(slither, [], FilteringAction.REJECT)
    assert not output

    # Then, if we run on everything, lets check that we get all
    output = run_detector_for_filtering(slither, [], FilteringAction.ALLOW)
    assert not output ^ {
        "A.constructor",
        "A.a",
        "B.constructor",
        "B.b",
        "C.constructor",
        "C.c",
        "D.constructor",
        "E.constructor",
    }

    # Then, test more closely
    # Reject all but a single directory
    output = run_detector_for_filtering(
        slither,
        [FilteringRule(type=FilteringAction.ALLOW, path=re.compile(r"sub1/"))],
        FilteringAction.REJECT,
    )
    assert not output ^ {"B.b", "A.constructor", "B.constructor", "A.a"}

    # Allow all but deny a directory
    output = run_detector_for_filtering(
        slither,
        [FilteringRule(type=FilteringAction.REJECT, path=re.compile(r"sub1/"))],
        FilteringAction.ALLOW,
    )
    assert not output ^ {"C.c", "C.constructor", "D.constructor", "E.constructor"}

    # Allow all functions named constructor
    output = run_detector_for_filtering(
        slither,
        [FilteringRule(type=FilteringAction.ALLOW, function=re.compile(r"constructor"))],
        FilteringAction.REJECT,
    )
    assert not output ^ {
        "A.constructor",
        "B.constructor",
        "C.constructor",
        "D.constructor",
        "E.constructor",
    }

    # Allow only contract C
    output = run_detector_for_filtering(
        slither,
        [FilteringRule(type=FilteringAction.ALLOW, contract=re.compile(r"C"))],
        FilteringAction.REJECT,
    )
    assert not output ^ {"C.constructor", "C.c"}

    # Allow everything in sub1 but not in sub1/sub12
    output = run_detector_for_filtering(
        slither,
        [
            FilteringRule(type=FilteringAction.ALLOW, path=re.compile("sub1/")),
            FilteringRule(type=FilteringAction.REJECT, path=re.compile("sub12/")),
        ],
        FilteringAction.REJECT,
    )
    assert not output ^ {"A.constructor", "A.a"}

    # Allow everything in D.sol
    output = run_detector_for_filtering(
        slither,
        [
            FilteringRule(type=FilteringAction.ALLOW, path=re.compile("D.sol")),
        ],
        FilteringAction.REJECT,
    )
    assert not output ^ {"D.constructor", "E.constructor"}

    # Allow only E in D.sol
    output = run_detector_for_filtering(
        slither,
        [
            FilteringRule(
                type=FilteringAction.ALLOW, path=re.compile("D.sol"), contract=re.compile("E")
            ),
        ],
        FilteringAction.REJECT,
    )
    assert not output ^ {"E.constructor"}


def get_default_namespace(
    include_paths: Union[str, None] = None,
    filter_paths: Union[str, None] = None,
    include: Union[str, None] = None,
    remove: Union[str, None] = None,
    filter_arg: Union[str, None] = None,
) -> Namespace:
    return Namespace(
        include_paths=include_paths,
        filter_paths=filter_paths,
        include=include,
        remove=remove,
        filter=filter_arg,
    )


def test_filtering_cl_deprecated(caplog):
    with caplog.at_level(logging.INFO):
        parsed_args = parse_filter_paths(get_default_namespace(include_paths="sub1/"))

    assert parsed_args == [FilteringRule(path=re.compile("sub1/"))]
    assert "include-paths is deprecated" in caplog.text

    with caplog.at_level(logging.INFO):
        parsed_args = parse_filter_paths(get_default_namespace(filter_paths="sub1/"))

    assert parsed_args == [FilteringRule(type=FilteringAction.REJECT, path=re.compile("sub1/"))]
    assert "filter-paths is deprecated" in caplog.text


def test_filtering_cl_multiple():
    parsed_args = parse_filter_paths(get_default_namespace(include="sub12/,sub2/"))

    assert parsed_args == [
        FilteringRule(type=FilteringAction.ALLOW, path=re.compile("sub12/")),
        FilteringRule(type=FilteringAction.ALLOW, path=re.compile("sub2/")),
    ]

    parsed_args = parse_filter_paths(get_default_namespace(remove="sub12/,sub2/"))

    assert parsed_args == [
        FilteringRule(type=FilteringAction.REJECT, path=re.compile("sub12/")),
        FilteringRule(type=FilteringAction.REJECT, path=re.compile("sub2/")),
    ]


def test_filtering_cl_full():
    parsed_args = parse_filter_paths(get_default_namespace(include="sub1/A.sol:A.a"))
    assert parsed_args == [
        FilteringRule(
            type=FilteringAction.ALLOW,
            path=re.compile("sub1/A.sol"),
            contract=re.compile("A"),
            function=re.compile("a"),
        ),
    ]

    parsed_args = parse_filter_paths(get_default_namespace(remove="sub1/A.sol:A.a"))
    assert parsed_args == [
        FilteringRule(
            type=FilteringAction.REJECT,
            path=re.compile("sub1/A.sol"),
            contract=re.compile("A"),
            function=re.compile("a"),
        ),
    ]


def test_filtering_cl_filter():
    parsed_args = parse_filter_paths(get_default_namespace(filter_arg="sub1/,-sub1/sub12/"))
    assert parsed_args == [
        FilteringRule(
            type=FilteringAction.ALLOW,
            path=re.compile("sub1/"),
        ),
        FilteringRule(
            type=FilteringAction.REJECT,
            path=re.compile("sub1/sub12/"),
        ),
    ]


def test_invalid_regex():
    with pytest.raises(ValueError):
        parse_filter_paths(get_default_namespace(filter_arg="sub1(/"))

    with pytest.raises(ValueError):
        parse_filter_paths(get_default_namespace(filter_arg=":not-matching:"))


@pytest.mark.skipif(
    not foundry_available or not project_ready, reason="requires Foundry and project setup"
)
def test_filtering_printer():
    def run_printer(
        sl: Slither, filtering_rules: List[FilteringRule], default_action: FilteringAction
    ):
        sl.filters = filtering_rules
        # pylint: disable=protected-access
        sl._contracts = []  # Reset the list of contracts so it gets recomputed
        sl.default_action = default_action
        return DummyPrinter.analyze_dummy_output(sl.run_printers().pop())

    slither = Slither(Path(TEST_DATA_DIR, "test_filtering").as_posix())
    slither.register_printer(DummyPrinter)

    output = run_printer(slither, [], FilteringAction.ALLOW)
    assert not output ^ {
        "A.a",
        "A.constructor",
        "B.b",
        "B.constructor",
        "C.c",
        "C.constructor",
        "D.constructor",
        "E.constructor",
    }

    # First, check that if we deny everything, we don't run on anything
    slither.default_action = FilteringAction.REJECT
    output = run_printer(slither, [], FilteringAction.REJECT)
    assert output == {""}

    # Then, test more closely
    # Reject all but a single directory
    output = run_printer(
        slither,
        [FilteringRule(type=FilteringAction.ALLOW, path=re.compile(r"sub1/"))],
        FilteringAction.REJECT,
    )
    assert not output ^ {"B.b", "A.constructor", "B.constructor", "A.a"}

    # Allow all but deny a directory
    output = run_printer(
        slither,
        [FilteringRule(type=FilteringAction.REJECT, path=re.compile(r"sub1/"))],
        FilteringAction.ALLOW,
    )
    assert not output ^ {"C.c", "C.constructor", "D.constructor", "E.constructor"}

    # Allow all functions named constructor
    output = run_printer(
        slither,
        [FilteringRule(type=FilteringAction.ALLOW, function=re.compile(r"constructor"))],
        FilteringAction.REJECT,
    )
    assert not output ^ {
        "A.constructor",
        "B.constructor",
        "C.constructor",
        "D.constructor",
        "E.constructor",
    }

    # Allow only contract C
    output = run_printer(
        slither,
        [FilteringRule(type=FilteringAction.ALLOW, contract=re.compile(r"C"))],
        FilteringAction.REJECT,
    )
    assert not output ^ {"C.constructor", "C.c"}

    # Allow everything in sub1 but not in sub1/sub12
    output = run_printer(
        slither,
        [
            FilteringRule(type=FilteringAction.ALLOW, path=re.compile("sub1/")),
            FilteringRule(type=FilteringAction.REJECT, path=re.compile("sub12/")),
        ],
        FilteringAction.REJECT,
    )
    assert not output ^ {"A.constructor", "A.a"}

    # Allow everything in D.sol
    output = run_printer(
        slither,
        [
            FilteringRule(type=FilteringAction.ALLOW, path=re.compile("D.sol")),
        ],
        FilteringAction.REJECT,
    )
    assert not output ^ {"D.constructor", "E.constructor"}

    # Allow only E in D.sol
    output = run_printer(
        slither,
        [
            FilteringRule(
                type=FilteringAction.ALLOW, path=re.compile("D.sol"), contract=re.compile("E")
            ),
        ],
        FilteringAction.REJECT,
    )
    assert not output ^ {"E.constructor"}


@pytest.mark.skipif(
    not foundry_available
    or not Path(TEST_DATA_DIR, "test_filtering_analysis/lib/forge-std").exists(),
    reason="requires Foundry and project setup",
)
def test_filtering_file_before_parsing():
    slither = Slither(
        Path(TEST_DATA_DIR, "test_filtering_analysis").as_posix(),
        filters=[
            FilteringRule(
                type=FilteringAction.REJECT,
                path=re.compile("sub2/"),
            ),
        ],
    )

    slither.register_printer(DummyPrinter)
    printer_output = DummyPrinter.analyze_dummy_output(slither.run_printers().pop())

    # We want to not get any results in sub2 but still manage to analyze A that depends on B.
    assert not printer_output ^ {
        "A.a",
        "A.constructor",
        "C.constructor",
        "E.constructor",
        "F.constructor",
    }
