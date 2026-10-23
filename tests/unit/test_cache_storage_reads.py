"""Precision and CLI regression tests for cache-storage-reads."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

import pytest
from crytic_compile.utils.zip import load_from_zip
from slither import Slither
from slither.__main__ import choose_detectors, get_detectors_and_printers
from slither.detectors.all_detectors import GasCacheStorageReads

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "tests/e2e/detectors/test_data/cache-storage-reads"
EXPECTED = {"doWhileRead", "conditionRead", "invariantRead", "whileRead"}


@pytest.fixture(params=["0.8.20", "0.8.30"])
def compiler_version(request):
    return request.param


def findings(version):
    compilation = load_from_zip(
        str(DATA / version / "cache_storage_reads.sol-VERSION.zip".replace("VERSION", version))
    )[0]
    slither = Slither(compilation)
    slither.register_detector(GasCacheStorageReads)
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
    assert all(r["check"] == "cache-storage-reads" for r in results)


def test_deterministic_output(compiler_version):
    assert findings(compiler_version) == findings(compiler_version)


def test_registered_detector():
    available, _ = get_detectors_and_printers()
    assert choose_detectors(
        argparse.Namespace(detectors_to_run="cache-storage-reads"), available
    ) == {GasCacheStorageReads}


def test_cli_and_json(compiler_version, solc_binary_path):
    target = DATA / compiler_version / "cache_storage_reads.sol"
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
            "cache-storage-reads",
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
