"""Precision and CLI regression tests for costly-loop."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

import pytest
from crytic_compile.utils.zip import load_from_zip
from slither import Slither
from slither.__main__ import choose_detectors, get_detectors_and_printers
from slither.detectors.all_detectors import CostlyOperationsInLoop

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "tests/e2e/detectors/test_data/costly-loop"
EXPECTED = {"withBreak", "doWhileWrite", "withContinue", "accumulate"}


@pytest.fixture(params=["0.8.20", "0.8.30"])
def compiler_version(request):
    return request.param


def findings(version):
    compilation = load_from_zip(
        str(DATA / version / "cacheable_accumulators.sol-VERSION.zip".replace("VERSION", version))
    )[0]
    slither = Slither(compilation)
    slither.register_detector(CostlyOperationsInLoop)
    return slither.run_detectors()[0]


def selected_results(results):
    return [r for r in results if r.get("additional_fields", {}).get("cacheable_accumulators")]


def reported(results):
    return {
        element["name"]
        for result in selected_results(results)
        for element in result["elements"]
        if element["type"] == "function"
    }


def test_exact_findings_exclude_negative_cases(compiler_version):
    results = findings(compiler_version)
    assert reported(results) == EXPECTED
    assert len(selected_results(results)) == len(EXPECTED)
    assert all(r["check"] == "costly-loop" for r in results)


def test_deterministic_output(compiler_version):
    assert findings(compiler_version) == findings(compiler_version)


def test_registered_detector():
    available, _ = get_detectors_and_printers()
    assert choose_detectors(argparse.Namespace(detectors_to_run="costly-loop"), available) == {
        CostlyOperationsInLoop
    }


def test_cli_and_json(compiler_version, solc_binary_path):
    target = DATA / compiler_version / "cacheable_accumulators.sol"
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "slither",
            str(target),
            "--compile-force-framework",
            "solc",
            "--solc",
            solc_binary_path(compiler_version),
            "--detect",
            "costly-loop",
            "--json",
            "-",
            "--fail-none",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    output = json.loads(process.stdout)
    assert output["success"], output
    assert reported(output["results"]["detectors"]) == EXPECTED
