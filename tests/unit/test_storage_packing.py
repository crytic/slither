"""Precision and CLI regression tests for storage-packing."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

import pytest
from crytic_compile.utils.zip import load_from_zip
from slither import Slither
from slither.__main__ import choose_detectors, get_detectors_and_printers
from slither.detectors.all_detectors import GasStoragePacking

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "tests/e2e/detectors/test_data/storage-packing"
EXPECTED = {"UnpackedStruct", "MixedWidths", "Unpacked"}


@pytest.fixture(params=["0.8.20", "0.8.30"])
def compiler_version(request):
    return request.param


def findings(version):
    compilation = load_from_zip(
        str(DATA / version / "storage_packing.sol-VERSION.zip".replace("VERSION", version))
    )[0]
    slither = Slither(compilation)
    slither.register_detector(GasStoragePacking)
    return slither.run_detectors()[0]


def selected_results(results):
    return results


def reported(results):
    return {
        element["name"]
        for result in selected_results(results)
        for element in result["elements"]
        if element["type"] in ("contract", "struct")
    }


def test_exact_findings_exclude_negative_cases(compiler_version):
    results = findings(compiler_version)
    assert reported(results) == EXPECTED
    assert len(selected_results(results)) == len(EXPECTED)
    assert all(r["check"] == "storage-packing" for r in results)


def test_deterministic_output(compiler_version):
    assert findings(compiler_version) == findings(compiler_version)


def test_registered_detector():
    available, _ = get_detectors_and_printers()
    assert choose_detectors(argparse.Namespace(detectors_to_run="storage-packing"), available) == {
        GasStoragePacking
    }


def test_cli_and_json(compiler_version, solc_binary_path):
    target = DATA / compiler_version / "storage_packing.sol"
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
            "storage-packing",
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


def test_slot_counts(compiler_version):
    for result in findings(compiler_version):
        assert result["additional_fields"]["slots_before"] == 3
        assert result["additional_fields"]["slots_after"] == 2
        assert len(result["additional_fields"]["suggested_order"]) >= 3
        assert "corrupt data" in result["description"]


def test_suggestion_matches_compiler_layout(compiler_version, solc_binary_path):
    source = """pragma solidity ^0.8.0;
    contract Before { uint128 a; uint256 b; uint128 c; }
    contract After { uint256 b; uint128 a; uint128 c; }
    """
    config = {
        "language": "Solidity",
        "sources": {"Packing.sol": {"content": source}},
        "settings": {"outputSelection": {"*": {"*": ["storageLayout"]}}},
    }
    result = subprocess.run(
        [solc_binary_path(compiler_version), "--standard-json"],
        input=json.dumps(config),
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(result.stdout)
    assert not [e for e in output.get("errors", []) if e["severity"] == "error"]
    contracts = output["contracts"]["Packing.sol"]
    assert {v["slot"] for v in contracts["Before"]["storageLayout"]["storage"]} == {"0", "1", "2"}
    assert {v["slot"] for v in contracts["After"]["storageLayout"]["storage"]} == {"0", "1"}
