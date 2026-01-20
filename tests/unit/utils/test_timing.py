"""Unit tests for slither.utils.timing module."""

import json
import threading
import time

import pytest

from slither.utils.timing import PhaseTimer


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the PhaseTimer singleton before and after each test."""
    PhaseTimer._instance = None
    yield
    PhaseTimer._instance = None


def test_phase_timer_disabled_by_default():
    """Timer should be disabled by default."""
    timer = PhaseTimer.get()
    assert timer.enabled is False


def test_phase_timer_no_collection_when_disabled():
    """Timer should not collect timing data when disabled."""
    timer = PhaseTimer.get()
    assert timer.enabled is False

    with timer.phase("test_phase"):
        time.sleep(0.01)

    assert len(timer.timings) == 0


def test_phase_timer_collects_when_enabled():
    """Timer should collect timing data when enabled."""
    timer = PhaseTimer.get()
    timer.enabled = True

    with timer.phase("test_phase"):
        time.sleep(0.01)

    assert "test_phase" in timer.timings
    assert len(timer.timings["test_phase"]) == 1
    # Use lenient threshold (0.008) for Windows timer resolution imprecision
    assert timer.timings["test_phase"][0] >= 0.008


def test_phase_timer_multiple_calls():
    """Timer should accumulate multiple calls to the same phase."""
    timer = PhaseTimer.get()
    timer.enabled = True

    for _ in range(3):
        with timer.phase("repeated_phase"):
            time.sleep(0.001)

    assert "repeated_phase" in timer.timings
    assert len(timer.timings["repeated_phase"]) == 3


def test_phase_timer_report_structure():
    """Report should have correct structure with count, total_sec, and avg_sec."""
    timer = PhaseTimer.get()
    timer.enabled = True

    with timer.phase("phase_a"):
        time.sleep(0.01)

    with timer.phase("phase_b"):
        time.sleep(0.02)

    report = timer.report()

    assert "phase_a" in report
    assert "phase_b" in report

    for phase_name in ["phase_a", "phase_b"]:
        assert "count" in report[phase_name]
        assert "total_sec" in report[phase_name]
        assert "avg_sec" in report[phase_name]
        assert report[phase_name]["count"] == 1


def test_phase_timer_report_text_format():
    """Report text should be human-readable with proper formatting."""
    timer = PhaseTimer.get()
    timer.enabled = True

    with timer.phase("my_phase"):
        time.sleep(0.01)

    text = timer.report_text()

    assert "Phase Timing Report:" in text
    assert "my_phase" in text
    assert "s" in text  # Time suffix


def test_phase_timer_reset():
    """Reset should clear all timing data."""
    timer = PhaseTimer.get()
    timer.enabled = True

    with timer.phase("phase_to_clear"):
        time.sleep(0.001)

    assert len(timer.timings) == 1

    timer.reset()

    assert len(timer.timings) == 0


def test_phase_timer_singleton():
    """PhaseTimer.get() should always return the same instance."""
    timer1 = PhaseTimer.get()
    timer2 = PhaseTimer.get()

    assert timer1 is timer2


def test_phase_timer_singleton_thread_safe():
    """Singleton should be thread-safe under concurrent access."""
    instances = []
    errors = []

    def get_instance():
        try:
            instance = PhaseTimer.get()
            instances.append(instance)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=get_instance) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(instances) == 10
    # All instances should be the same object
    assert all(inst is instances[0] for inst in instances)


def test_phase_timer_report_json():
    """report_json() should return valid JSON string."""
    timer = PhaseTimer.get()
    timer.enabled = True

    with timer.phase("json_test"):
        time.sleep(0.001)

    json_str = timer.report_json()
    parsed = json.loads(json_str)

    assert "json_test" in parsed
    assert parsed["json_test"]["count"] == 1


def test_phase_timer_report_sorted_by_total_time():
    """Report should be sorted by total time in descending order."""
    timer = PhaseTimer.get()
    timer.enabled = True

    with timer.phase("short"):
        time.sleep(0.001)

    with timer.phase("long"):
        time.sleep(0.02)

    report = timer.report()
    phases = list(report.keys())

    # "long" should come before "short" since it has more total time
    assert phases.index("long") < phases.index("short")


def test_phase_timer_multiple_phases_text():
    """Report text should show call count and average for multiple calls."""
    timer = PhaseTimer.get()
    timer.enabled = True

    for _ in range(3):
        with timer.phase("multi_call"):
            time.sleep(0.001)

    text = timer.report_text()

    assert "3 calls" in text
    assert "avg" in text
