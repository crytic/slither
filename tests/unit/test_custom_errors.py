"""Precision and CLI regression tests for custom-errors."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

import pytest
from crytic_compile.utils.zip import load_from_zip
from slither import Slither
from slither.__main__ import choose_detectors, get_detectors_and_printers
from slither.detectors.all_detectors import GasCustomErrors

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "tests/e2e/detectors/test_data/custom-errors"
EXPECTED = {"topLevelRequire", "inheritedRevert", "literalRevert", "allowed", "literalRequire"}


@pytest.fixture(params=["0.8.20", "0.8.30"])
def compiler_version(request):
    return request.param


def findings(version):
    compilation = load_from_zip(
        str(DATA / version / "custom_errors.sol-VERSION.zip".replace("VERSION", version))
    )[0]
    slither = Slither(compilation)
    slither.register_detector(GasCustomErrors)
    return slither.run_detectors()[0]


def selected_results(results):
    return results


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
    assert all(r["check"] == "custom-errors" for r in results)


def test_deterministic_output(compiler_version):
    assert findings(compiler_version) == findings(compiler_version)


def test_registered_detector():
    available, _ = get_detectors_and_printers()
    assert choose_detectors(argparse.Namespace(detectors_to_run="custom-errors"), available) == {
        GasCustomErrors
    }


def test_cli_and_json(compiler_version, solc_binary_path):
    target = DATA / compiler_version / "custom_errors.sol"
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
            "custom-errors",
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


def test_legacy_compiler_is_excluded():
    path = (
        ROOT
        / "tests/e2e/detectors/test_data/domain-separator-collision/0.5.16/permit_domain_collision.sol-0.5.16.zip"
    )
    slither = Slither(load_from_zip(str(path))[0])
    slither.register_detector(GasCustomErrors)
    assert slither.run_detectors()[0] == []
