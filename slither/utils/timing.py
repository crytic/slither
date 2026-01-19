"""Fine-grained timing instrumentation for Slither phases."""

import json
import threading
import time
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager


class PhaseTimer:
    """Singleton for collecting timing data across Slither phases."""

    _instance: "PhaseTimer | None" = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self.timings: dict[str, list[float]] = defaultdict(list)
        self.enabled = False

    @classmethod
    def get(cls) -> "PhaseTimer":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = PhaseTimer()
        return cls._instance

    @contextmanager
    def phase(self, name: str) -> Generator[None, None, None]:
        """Context manager to time a named phase."""
        if not self.enabled:
            yield
            return
        start = time.perf_counter()
        try:
            yield
        finally:
            self.timings[name].append(time.perf_counter() - start)

    def report(self) -> dict[str, dict]:
        """Return timing statistics sorted by total time."""
        return {
            name: {
                "count": len(times),
                "total_sec": round(sum(times), 3),
                "avg_sec": round(sum(times) / len(times), 3) if times else 0,
            }
            for name, times in sorted(self.timings.items(), key=lambda x: sum(x[1]), reverse=True)
        }

    def report_json(self) -> str:
        return json.dumps(self.report(), indent=2)

    def report_text(self) -> str:
        """Return human-readable timing report."""
        lines = ["Phase Timing Report:"]
        for name, stats in self.report().items():
            total = stats["total_sec"]
            count = stats["count"]
            avg = stats["avg_sec"]
            if count == 1:
                lines.append(f"  {name}: {total:.3f}s")
            else:
                lines.append(f"  {name}: {total:.3f}s ({count} calls, avg {avg:.3f}s)")
        return "\n".join(lines)

    def reset(self) -> None:
        """Clear all timing data."""
        self.timings.clear()
