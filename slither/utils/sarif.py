"""
Various utils for sarif/vscode
"""
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any


def _parse_index(key: str) -> Optional[Tuple[int, int]]:
    if key.count(":") != 2:
        return None

    try:
        run = int(key[key.find(":") + 1 : key.rfind(":")])
        index = int(key[key.rfind(":") + 1 :])
        return run, index
    except ValueError:
        return None


def _get_indexes(path_to_triage: Path) -> List[Tuple[int, int]]:
    try:
        with open(path_to_triage, encoding="utf8") as file_desc:
            triage = json.load(file_desc)
    except json.decoder.JSONDecodeError:
        return []

    resultIdToNotes: Dict[str, Dict] = triage.get("resultIdToNotes", {})

    indexes: List[Tuple[int, int]] = []
    for key, data in resultIdToNotes.items():
        if "status" in data and data["status"] == 1:
            parsed = _parse_index(key)
            if parsed:
                indexes.append(parsed)

    return indexes


def read_triage_info(path_to_sarif: Path, path_to_triage: Path) -> List[str]:
    try:
        with open(path_to_sarif, encoding="utf8") as file_desc:
            sarif = json.load(file_desc)
    except json.decoder.JSONDecodeError:
        return []

    runs: List[Dict[str, Any]] = sarif.get("runs", [])

    # Don't support multiple runs for now
    if len(runs) != 1:
        return []

    run_results: List[Dict] = runs[0].get("results", [])

    indexes = _get_indexes(path_to_triage)

    ids: List[str] = []
    for run, index in indexes:

        # We dont support multiple runs for now
        if run != 0:
            continue
        try:
            elem = run_results[index]
        except KeyError:
            continue
        if "partialFingerprints" in elem:
            if "id" in elem["partialFingerprints"]:
                ids.append(elem["partialFingerprints"]["id"])

    return ids
