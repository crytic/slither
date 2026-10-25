import json

import pytest

from slither.core.slither_core import SlitherCore
from slither.utils.sarif import read_triage_info


@pytest.mark.parametrize("invalid_index", [-1, 2, 100])
def test_ignore_invalid_result_indexes_and_keep_valid_triage(tmp_path, invalid_index):
    sarif = tmp_path / "report.sarif"
    triage = tmp_path / "report.sarif.triage"
    sarif.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "results": [
                            {"partialFingerprints": {"id": "keep-hidden"}},
                            {"partialFingerprints": {"id": "keep-visible"}},
                        ]
                    }
                ]
            }
        ),
        encoding="utf8",
    )
    triage.write_text(
        json.dumps(
            {
                "resultIdToNotes": {
                    f"report:0:{invalid_index}": {"status": 1},
                    "report:0:0": {"status": 1},
                    "report:0:1": {"status": 0},
                    "report:1:1": {"status": 1},
                }
            }
        ),
        encoding="utf8",
    )

    assert read_triage_info(sarif, triage) == ["keep-hidden"]
    core = SlitherCore()
    core.sarif_input = str(sarif)
    core.sarif_triage = str(triage)
    core.load_previous_results_from_sarif()
    assert core._previous_results_ids == {"keep-hidden"}


def test_ignore_stale_triage_when_report_has_no_results(tmp_path):
    sarif = tmp_path / "report.sarif"
    triage = tmp_path / "report.sarif.triage"
    sarif.write_text(json.dumps({"runs": [{"results": []}]}), encoding="utf8")
    triage.write_text(
        json.dumps({"resultIdToNotes": {"report:0:0": {"status": 1}}}),
        encoding="utf8",
    )
    assert read_triage_info(sarif, triage) == []
