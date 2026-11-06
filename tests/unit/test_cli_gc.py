import gc
import subprocess
import sys
import weakref

import pytest

from slither import __main__ as cli


def reported(*thresholds):
    """Return thresholds as gc.get_threshold() reports them.

    CPython 3.14 has two generations and reports the third threshold as 0.
    """
    previous = gc.get_threshold()
    gc.set_threshold(*thresholds)
    try:
        return gc.get_threshold()
    finally:
        gc.set_threshold(*previous)


@pytest.fixture
def gc_policy():
    thresholds, enabled = gc.get_threshold(), gc.isenabled()
    try:
        yield
    finally:
        gc.set_threshold(*thresholds)
        (gc.enable if enabled else gc.disable)()


@pytest.mark.parametrize("stage", ["plugins", "analysis"])
@pytest.mark.parametrize("error", [None, SystemExit(0), SystemExit(-1), RuntimeError("failure")])
def test_cli_restores_gc_policy(monkeypatch, gc_policy, stage, error):
    gc.set_threshold(1234, 17, 19)
    detectors, printers = [], []

    def check_policy():
        assert gc.get_threshold() == reported(200_000, 30, 30)
        if error is not None:
            raise error

    def plugins():
        if stage == "plugins":
            check_policy()
        return detectors, printers

    def analysis(*, all_detector_classes, all_printer_classes):
        assert all_detector_classes is detectors
        assert all_printer_classes is printers
        if stage == "analysis":
            check_policy()

    monkeypatch.setattr(cli, "get_detectors_and_printers", plugins)
    monkeypatch.setattr(cli, "main_impl", analysis)
    if error is None:
        cli.main()
    else:
        with pytest.raises(type(error)) as caught:
            cli.main()
        assert caught.value is error
    assert gc.get_threshold() == reported(1234, 17, 19)


@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize("thresholds", [(0, 10, 10), (300_000, 40, 50)])
def test_cli_respects_disabled_gc_and_larger_thresholds(
    monkeypatch, gc_policy, enabled, thresholds
):
    gc.set_threshold(*thresholds)
    (gc.enable if enabled else gc.disable)()
    if not enabled or not thresholds[0]:
        monkeypatch.setattr(gc, "collect", lambda: pytest.fail("collection was disabled"))
    monkeypatch.setattr(cli, "get_detectors_and_printers", lambda: ([], []))

    def analysis(**kwargs):
        assert gc.isenabled() is enabled
        assert gc.get_threshold() == reported(*thresholds)

    monkeypatch.setattr(cli, "main_impl", analysis)
    cli.main()
    assert gc.isenabled() is enabled
    assert gc.get_threshold() == reported(*thresholds)


def test_import_does_not_change_gc_policy():
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import gc; gc.set_threshold(1234, 17, 19); gc.disable(); before = gc.get_threshold(); "
            "import slither; import slither.__main__; "
            "assert gc.get_threshold() == before; assert not gc.isenabled()",
        ],
        check=True,
    )


def test_cli_keeps_gc_disabled_with_small_thresholds(monkeypatch, gc_policy):
    gc.set_threshold(1234, 17, 19)
    gc.disable()
    monkeypatch.setattr(gc, "collect", lambda: pytest.fail("collection was disabled"))
    monkeypatch.setattr(cli, "get_detectors_and_printers", lambda: ([], []))

    def analysis(**kwargs):
        assert not gc.isenabled()

    monkeypatch.setattr(cli, "main_impl", analysis)
    cli.main()
    assert not gc.isenabled()
    assert gc.get_threshold() == reported(1234, 17, 19)


def test_cli_releases_cycles_from_previous_invocations(monkeypatch, gc_policy):
    gc.enable()
    gc.set_threshold(1_000_000_000, 1_000_000_000, 1_000_000_000)
    references = []

    class Model:
        def __init__(self):
            self.cycle = self

    def analysis(**kwargs):
        assert all(reference() is None for reference in references)
        model = Model()
        references.append(weakref.ref(model))

    monkeypatch.setattr(cli, "get_detectors_and_printers", lambda: ([], []))
    monkeypatch.setattr(cli, "main_impl", analysis)
    for _ in range(3):
        cli.main()
        assert references[-1]() is not None


def test_library_analysis_does_not_change_gc_policy(gc_policy, slither_from_solidity_source):
    gc.set_threshold(1234, 17, 19)
    with slither_from_solidity_source("pragma solidity ^0.8.19; contract C {}") as slither:
        assert slither.get_contract_from_name("C")
        assert gc.get_threshold() == reported(1234, 17, 19)
