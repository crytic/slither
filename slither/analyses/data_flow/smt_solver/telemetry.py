"""Telemetry for SMT solver operations.

This module provides counters and timing instrumentation for tracking
solver performance, useful for identifying bottlenecks in the interval analysis.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Optional
from contextlib import contextmanager


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    hits: int
    misses: int
    total_queries: int
    hit_rate: float


@dataclass
class OptimizerReuseMetrics:
    """Optimizer instance reuse metrics."""

    instances_created: int
    instances_reused: int
    push_pop_operations: int


@dataclass
class PerformanceMetrics:
    """Overall performance metrics."""

    queries_avoided: int
    assertions_copied: int


@dataclass
class OptimizationMetrics:
    """Complete optimization effectiveness metrics."""

    cache: CacheMetrics
    optimizer_reuse: OptimizerReuseMetrics
    performance: PerformanceMetrics


@dataclass
class SolverTelemetry:
    """Tracks SMT solver operation counts and timing.

    Usage:
        telemetry = SolverTelemetry()

        # Count operations
        telemetry.count("assert_constraint")
        telemetry.count("check_sat")

        # Time operations
        with telemetry.time("optimize_min"):
            # ... expensive operation ...
            pass

        # Print summary
        telemetry.print_summary()
    """

    # Operation counters
    counts: Dict[str, int] = field(default_factory=dict)

    # Timing accumulators (total time in seconds)
    timings: Dict[str, float] = field(default_factory=dict)

    # Timing call counts (for computing averages)
    timing_counts: Dict[str, int] = field(default_factory=dict)

    # Whether telemetry is enabled
    enabled: bool = True

    def count(self, operation: str, amount: int = 1) -> None:
        """Increment counter for an operation."""
        if not self.enabled:
            return
        self.counts[operation] = self.counts.get(operation, 0) + amount

    @contextmanager
    def time(self, operation: str):
        """Context manager to time an operation."""
        if not self.enabled:
            yield
            return

        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.timings[operation] = self.timings.get(operation, 0.0) + elapsed
            self.timing_counts[operation] = self.timing_counts.get(operation, 0) + 1

    def reset(self) -> None:
        """Reset all counters and timings."""
        self.counts.clear()
        self.timings.clear()
        self.timing_counts.clear()

    def get_summary(self) -> Dict[str, Dict]:
        """Get summary of all telemetry data."""
        summary = {
            "counts": dict(self.counts),
            "timings": {},
        }

        for op, total_time in self.timings.items():
            call_count = self.timing_counts.get(op, 1)
            summary["timings"][op] = {
                "total_seconds": round(total_time, 4),
                "call_count": call_count,
                "avg_ms": round((total_time / call_count) * 1000, 2) if call_count > 0 else 0,
            }

        return summary

    def get_optimization_metrics(self) -> OptimizationMetrics:
        """Get metrics showing optimization effectiveness.

        Returns:
            OptimizationMetrics with cache stats and query reduction metrics
        """
        cache_hits = self.counts.get("cache_hit", 0)
        cache_misses = self.counts.get("cache_miss", 0)
        total_queries = cache_hits + cache_misses
        hit_rate = round((cache_hits / total_queries * 100) if total_queries > 0 else 0, 2)

        cache_metrics = CacheMetrics(
            hits=cache_hits,
            misses=cache_misses,
            total_queries=total_queries,
            hit_rate=hit_rate,
        )

        optimize_created = self.counts.get("optimize_instance_created", 0)
        optimize_reused = self.counts.get("optimize_instance_reused", 0)
        push_pop_used = self.counts.get("push_pop_used", 0)

        optimizer_metrics = OptimizerReuseMetrics(
            instances_created=optimize_created,
            instances_reused=optimize_reused,
            push_pop_operations=push_pop_used,
        )

        assertions_copied = self.counts.get("assertions_copied", 0)
        queries_avoided = cache_hits

        perf_metrics = PerformanceMetrics(
            queries_avoided=queries_avoided,
            assertions_copied=assertions_copied,
        )

        return OptimizationMetrics(
            cache=cache_metrics,
            optimizer_reuse=optimizer_metrics,
            performance=perf_metrics,
        )

    def _print_rich_optimization(self, opt_metrics, console) -> None:
        """Print optimization metrics as a rich table."""
        from rich.table import Table

        has_cache = opt_metrics.cache.total_queries > 0
        has_optimizer = opt_metrics.optimizer_reuse.instances_created > 0
        if not (has_cache or has_optimizer):
            return

        table = Table(title="Optimization Metrics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")

        if opt_metrics.cache.total_queries > 0:
            table.add_row("Cache Hit Rate", f"{opt_metrics.cache.hit_rate:.2f}%")
            table.add_row("Cache Hits", str(opt_metrics.cache.hits))
            table.add_row("Cache Misses", str(opt_metrics.cache.misses))

        reuse = opt_metrics.optimizer_reuse
        if reuse.instances_created > 0 or reuse.push_pop_operations > 0:
            table.add_row("Optimizer Instances Created", str(reuse.instances_created))
            table.add_row("Optimizer Reuses (push/pop)", str(reuse.push_pop_operations))

        perf = opt_metrics.performance
        if perf.queries_avoided > 0:
            table.add_row("Queries Avoided (cached)", str(perf.queries_avoided))
        if perf.assertions_copied > 0:
            table.add_row("Assertions Copied", str(perf.assertions_copied))

        console.print(table)

    def _print_rich_counts(self, summary, console) -> None:
        """Print operation counts as a rich table."""
        from rich.table import Table

        if not summary["counts"]:
            return

        table = Table(title="SMT Solver Operation Counts", show_header=True)
        table.add_column("Operation", style="cyan")
        table.add_column("Count", justify="right", style="green")

        for op, count in sorted(summary["counts"].items(), key=lambda x: -x[1]):
            table.add_row(op, str(count))

        console.print(table)

    def _print_rich_timings(self, summary, console) -> None:
        """Print operation timings as a rich table."""
        from rich.table import Table

        if not summary["timings"]:
            return

        table = Table(title="SMT Solver Operation Timings", show_header=True)
        table.add_column("Operation", style="cyan")
        table.add_column("Total (s)", justify="right", style="yellow")
        table.add_column("Calls", justify="right", style="green")
        table.add_column("Avg (ms)", justify="right", style="magenta")

        sorted_timings = sorted(
            summary["timings"].items(), key=lambda x: -x[1]["total_seconds"]
        )
        for op, data in sorted_timings:
            table.add_row(
                op,
                f"{data['total_seconds']:.3f}",
                str(data["call_count"]),
                f"{data['avg_ms']:.2f}",
            )

        console.print(table)

    def _print_text_optimization(self, opt_metrics) -> None:
        """Print optimization metrics as plain text."""
        cache = opt_metrics.cache
        reuse = opt_metrics.optimizer_reuse
        perf = opt_metrics.performance

        if not (cache.total_queries > 0 or reuse.instances_created > 0):
            return

        print("\nOptimization Metrics:")
        if cache.total_queries > 0:
            print(f"  Cache Hit Rate: {cache.hit_rate:.2f}%")
            print(f"  Cache Hits: {cache.hits}")
            print(f"  Cache Misses: {cache.misses}")
        if reuse.instances_created > 0 or reuse.push_pop_operations > 0:
            print(f"  Optimizer Instances Created: {reuse.instances_created}")
            print(f"  Optimizer Reuses (push/pop): {reuse.push_pop_operations}")
        if perf.queries_avoided > 0 or perf.assertions_copied > 0:
            print(f"  Queries Avoided (cached): {perf.queries_avoided}")
            if perf.assertions_copied > 0:
                print(f"  Assertions Copied: {perf.assertions_copied}")

    def _print_text_counts(self, summary) -> None:
        """Print operation counts as plain text."""
        if not summary["counts"]:
            return

        print("\nOperation Counts:")
        for op, count in sorted(summary["counts"].items(), key=lambda x: -x[1]):
            print(f"  {op}: {count}")

    def _print_text_timings(self, summary) -> None:
        """Print operation timings as plain text."""
        if not summary["timings"]:
            return

        print("\nOperation Timings:")
        sorted_timings = sorted(
            summary["timings"].items(), key=lambda x: -x[1]["total_seconds"]
        )
        for op, data in sorted_timings:
            total = data['total_seconds']
            calls = data['call_count']
            avg = data['avg_ms']
            print(f"  {op}: {total:.3f}s total, {calls} calls, {avg:.2f}ms avg")

    def print_summary(self, console=None) -> None:
        """Print a formatted summary of telemetry data."""
        summary = self.get_summary()
        opt_metrics = self.get_optimization_metrics()

        if console:
            self._print_rich_optimization(opt_metrics, console)
            self._print_rich_counts(summary, console)
            self._print_rich_timings(summary, console)
        else:
            print("\n=== SMT Solver Telemetry ===")
            self._print_text_optimization(opt_metrics)
            self._print_text_counts(summary)
            self._print_text_timings(summary)
            print()


# Global telemetry instance (disabled by default)
_global_telemetry: Optional[SolverTelemetry] = None


def get_telemetry(create_if_missing: bool = True) -> Optional[SolverTelemetry]:
    """Get the global telemetry instance.

    Args:
        create_if_missing: If True, creates a new disabled instance if none exists.

    Returns:
        The global SolverTelemetry instance, or None if not created.
    """
    global _global_telemetry
    if _global_telemetry is None and create_if_missing:
        _global_telemetry = SolverTelemetry(enabled=False)
    return _global_telemetry


def enable_telemetry() -> SolverTelemetry:
    """Enable global telemetry and return the instance."""
    global _global_telemetry
    if _global_telemetry is None:
        _global_telemetry = SolverTelemetry(enabled=True)
    else:
        _global_telemetry.enabled = True
    return _global_telemetry


def disable_telemetry() -> None:
    """Disable global telemetry."""
    global _global_telemetry
    if _global_telemetry is not None:
        _global_telemetry.enabled = False


def reset_telemetry() -> None:
    """Reset global telemetry counters."""
    global _global_telemetry
    if _global_telemetry is not None:
        _global_telemetry.reset()
