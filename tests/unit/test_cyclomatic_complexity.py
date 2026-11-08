import logging
from types import SimpleNamespace
from unittest.mock import patch

from slither import __main__ as slither_main
from slither.detectors.functions.cyclomatic_complexity import CyclomaticComplexity


def _detector(threshold: int | None = None) -> CyclomaticComplexity:
    function = object()
    compilation_unit = SimpleNamespace(
        contracts=[SimpleNamespace(functions_declared=[function])],
        functions_top_level=[],
    )
    slither = SimpleNamespace()
    if threshold is not None:
        slither.cyclomatic_complexity_threshold = threshold
    detector = CyclomaticComplexity(compilation_unit, slither, logging.getLogger("test"))
    detector.generate_result = lambda info: info
    return detector


def test_default_cyclomatic_complexity_threshold_remains_11() -> None:
    detector = _detector()
    with patch(
        "slither.detectors.functions.cyclomatic_complexity.compute_cyclomatic_complexity",
        return_value=11,
    ):
        assert detector._detect() == []
    with patch(
        "slither.detectors.functions.cyclomatic_complexity.compute_cyclomatic_complexity",
        return_value=12,
    ):
        assert len(detector._detect()) == 1


def test_configured_cyclomatic_complexity_threshold_is_exclusive() -> None:
    detector = _detector(15)
    with patch(
        "slither.detectors.functions.cyclomatic_complexity.compute_cyclomatic_complexity",
        return_value=15,
    ):
        assert detector._detect() == []
    with patch(
        "slither.detectors.functions.cyclomatic_complexity.compute_cyclomatic_complexity",
        return_value=16,
    ):
        assert len(detector._detect()) == 1


def test_process_single_applies_configured_threshold(monkeypatch) -> None:
    fake_slither = SimpleNamespace()

    def fake_constructor(target, **kwargs):
        assert "cyclomatic_complexity_threshold" not in kwargs
        return fake_slither

    monkeypatch.setattr(slither_main, "Slither", fake_constructor)
    monkeypatch.setattr(
        slither_main,
        "_process",
        lambda slither, detector_classes, printer_classes, warn_unused_ignores=False: (
            slither,
            [],
            [],
            0,
        ),
    )
    args = SimpleNamespace(
        legacy_ast=False,
        cyclomatic_complexity_threshold=17,
        sarif_input=None,
        sarif_triage=None,
        warn_unused_ignores=False,
    )

    slither_main.process_single("target", args, [], [])

    assert fake_slither.cyclomatic_complexity_threshold == 17


def test_process_all_does_not_forward_detector_threshold_to_crytic_compile(monkeypatch) -> None:
    captured = {}

    def fake_compile_all(target, **kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(slither_main, "compile_all", fake_compile_all)
    args = SimpleNamespace(cyclomatic_complexity_threshold=17, compiler_flag=True)

    slither_main.process_all("target", args, [], [])

    assert captured == {"compiler_flag": True}
