"""Telemetry for SMT solver operations.

This module provides counters and timing instrumentation for tracking
solver performance, useful for identifying bottlenecks in the interval analysis.

Designed for evaluation with comprehensive metrics covering:
- Function-level characteristics (CFG nodes, loops, variables)
- Analysis convergence (worklist iterations, widening/narrowing)
- Constraint statistics (by type and complexity)
- Solver performance (SAT/UNSAT/timeout breakdown)
- Precision metrics (tight bounds vs full range)
"""

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
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
class FunctionMetrics:
    """Function-level characteristics."""

    name: str = ""
    cfg_nodes: int = 0
    basic_blocks: int = 0
    parameters: int = 0
    local_variables: int = 0
    state_variables_accessed: int = 0
    loops: int = 0
    external_calls: int = 0


@dataclass
class AnalysisMetrics:
    """Analysis convergence metrics."""

    worklist_iterations: int = 0
    widening_applications: int = 0
    narrowing_applications: int = 0
    fixpoint_reached: bool = False
    back_edges_detected: int = 0


@dataclass
class ConstraintMetrics:
    """SMT constraint statistics."""

    total_constraints: int = 0
    equality_constraints: int = 0
    inequality_constraints: int = 0
    arithmetic_constraints: int = 0
    overflow_predicates: int = 0
    path_constraints: int = 0
    bitvector_256bit: int = 0
    bitvector_other: int = 0


@dataclass
class SolverOutcomeMetrics:
    """Solver query outcome statistics."""

    sat_results: int = 0
    unsat_results: int = 0
    timeout_results: int = 0
    unknown_results: int = 0
    total_solver_time_ms: float = 0.0
    avg_query_time_ms: float = 0.0
    max_query_time_ms: float = 0.0
    min_query_time_ms: float = float("inf")


@dataclass
class TransferFunctionMetrics:
    """Transfer function operation statistics."""

    arithmetic_ops: int = 0
    comparison_ops: int = 0
    bitwise_ops: int = 0
    memory_ops: int = 0
    storage_ops: int = 0
    call_ops: int = 0
    assignment_ops: int = 0
    operations_handled: int = 0
    operations_skipped: int = 0


@dataclass
class PrecisionMetrics:
    """Analysis precision statistics."""

    variables_total: int = 0
    variables_with_precise_bounds: int = 0
    variables_with_full_range: int = 0
    overflow_warnings: int = 0
    underflow_warnings: int = 0
    precision_ratio: float = 0.0


@dataclass
class EvaluationMetrics:
    """Complete metrics for academic evaluation."""

    function: FunctionMetrics = field(default_factory=FunctionMetrics)
    analysis: AnalysisMetrics = field(default_factory=AnalysisMetrics)
    constraints: ConstraintMetrics = field(default_factory=ConstraintMetrics)
    solver: SolverOutcomeMetrics = field(default_factory=SolverOutcomeMetrics)
    transfer_functions: TransferFunctionMetrics = field(default_factory=TransferFunctionMetrics)
    precision: PrecisionMetrics = field(default_factory=PrecisionMetrics)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Export as JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


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

        # Record structured metrics
        telemetry.record_function_info(name="foo", cfg_nodes=10, loops=2)
        telemetry.record_solver_outcome("sat", elapsed_ms=150.0)
        telemetry.record_transfer_op("arithmetic")

        # Print summary
        telemetry.print_summary()

        # Export for academic evaluation
        json_output = telemetry.get_evaluation_metrics().to_json()
    """

    # Operation counters
    counts: Dict[str, int] = field(default_factory=dict)

    # Timing accumulators (total time in seconds)
    timings: Dict[str, float] = field(default_factory=dict)

    # Timing call counts (for computing averages)
    timing_counts: Dict[str, int] = field(default_factory=dict)

    # Whether telemetry is enabled
    enabled: bool = True

    # Structured evaluation metrics
    evaluation: EvaluationMetrics = field(default_factory=EvaluationMetrics)

    # Per-query timing for statistics
    _query_times_ms: List[float] = field(default_factory=list)

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

    # =========================================================================
    # Structured Metric Recording Methods
    # =========================================================================

    def record_function_info(
        self,
        name: str = "",
        cfg_nodes: int = 0,
        basic_blocks: int = 0,
        parameters: int = 0,
        local_variables: int = 0,
        state_variables_accessed: int = 0,
        loops: int = 0,
        external_calls: int = 0,
    ) -> None:
        """Record function-level characteristics."""
        if not self.enabled:
            return
        func = self.evaluation.function
        func.name = name
        func.cfg_nodes = cfg_nodes
        func.basic_blocks = basic_blocks
        func.parameters = parameters
        func.local_variables = local_variables
        func.state_variables_accessed = state_variables_accessed
        func.loops = loops
        func.external_calls = external_calls

    def record_worklist_iteration(self) -> None:
        """Record a worklist iteration."""
        if not self.enabled:
            return
        self.evaluation.analysis.worklist_iterations += 1

    def record_widening(self) -> None:
        """Record a widening application."""
        if not self.enabled:
            return
        self.evaluation.analysis.widening_applications += 1

    def record_narrowing(self) -> None:
        """Record a narrowing application."""
        if not self.enabled:
            return
        self.evaluation.analysis.narrowing_applications += 1

    def record_back_edge(self) -> None:
        """Record a back edge detection."""
        if not self.enabled:
            return
        self.evaluation.analysis.back_edges_detected += 1

    def record_fixpoint_reached(self) -> None:
        """Record that fixpoint was reached."""
        if not self.enabled:
            return
        self.evaluation.analysis.fixpoint_reached = True

    def record_constraint(
        self,
        constraint_type: str,
        bitvector_width: int = 256,
    ) -> None:
        """Record a constraint by type.

        Args:
            constraint_type: One of "equality", "inequality", "arithmetic",
                           "overflow", "path"
            bitvector_width: Width of bitvector (for tracking 256-bit vs other)
        """
        if not self.enabled:
            return
        constraints = self.evaluation.constraints
        constraints.total_constraints += 1

        if constraint_type == "equality":
            constraints.equality_constraints += 1
        elif constraint_type == "inequality":
            constraints.inequality_constraints += 1
        elif constraint_type == "arithmetic":
            constraints.arithmetic_constraints += 1
        elif constraint_type == "overflow":
            constraints.overflow_predicates += 1
        elif constraint_type == "path":
            constraints.path_constraints += 1

        if bitvector_width == 256:
            constraints.bitvector_256bit += 1
        else:
            constraints.bitvector_other += 1

    def record_solver_outcome(self, outcome: str, elapsed_ms: float) -> None:
        """Record a solver query outcome.

        Args:
            outcome: One of "sat", "unsat", "timeout", "unknown"
            elapsed_ms: Time taken for the query in milliseconds
        """
        if not self.enabled:
            return
        solver = self.evaluation.solver

        if outcome == "sat":
            solver.sat_results += 1
        elif outcome == "unsat":
            solver.unsat_results += 1
        elif outcome == "timeout":
            solver.timeout_results += 1
        elif outcome == "unknown":
            solver.unknown_results += 1

        solver.total_solver_time_ms += elapsed_ms
        self._query_times_ms.append(elapsed_ms)

        if elapsed_ms > solver.max_query_time_ms:
            solver.max_query_time_ms = elapsed_ms
        if elapsed_ms < solver.min_query_time_ms:
            solver.min_query_time_ms = elapsed_ms

    def record_transfer_op(self, op_category: str, handled: bool = True) -> None:
        """Record a transfer function operation.

        Args:
            op_category: One of "arithmetic", "comparison", "bitwise",
                        "memory", "storage", "call", "assignment"
            handled: Whether the operation was successfully handled
        """
        if not self.enabled:
            return
        transfer = self.evaluation.transfer_functions

        if op_category == "arithmetic":
            transfer.arithmetic_ops += 1
        elif op_category == "comparison":
            transfer.comparison_ops += 1
        elif op_category == "bitwise":
            transfer.bitwise_ops += 1
        elif op_category == "memory":
            transfer.memory_ops += 1
        elif op_category == "storage":
            transfer.storage_ops += 1
        elif op_category == "call":
            transfer.call_ops += 1
        elif op_category == "assignment":
            transfer.assignment_ops += 1

        if handled:
            transfer.operations_handled += 1
        else:
            transfer.operations_skipped += 1

    def record_precision(
        self,
        is_precise: bool,
        has_overflow: bool = False,
        has_underflow: bool = False,
    ) -> None:
        """Record precision information for a variable.

        Args:
            is_precise: True if bounds are tighter than full type range
            has_overflow: True if overflow is possible
            has_underflow: True if underflow is possible
        """
        if not self.enabled:
            return
        precision = self.evaluation.precision
        precision.variables_total += 1

        if is_precise:
            precision.variables_with_precise_bounds += 1
        else:
            precision.variables_with_full_range += 1

        if has_overflow:
            precision.overflow_warnings += 1
        if has_underflow:
            precision.underflow_warnings += 1

    def finalize_metrics(self) -> None:
        """Compute derived metrics (averages, ratios). Call after analysis."""
        if not self.enabled:
            return

        # Compute average query time
        solver = self.evaluation.solver
        total_queries = (
            solver.sat_results
            + solver.unsat_results
            + solver.timeout_results
            + solver.unknown_results
        )
        if total_queries > 0:
            solver.avg_query_time_ms = solver.total_solver_time_ms / total_queries

        # Handle min_query_time_ms if no queries were made
        if solver.min_query_time_ms == float("inf"):
            solver.min_query_time_ms = 0.0

        # Compute precision ratio
        precision = self.evaluation.precision
        if precision.variables_total > 0:
            precision.precision_ratio = (
                precision.variables_with_precise_bounds / precision.variables_total
            )

    def get_evaluation_metrics(self) -> EvaluationMetrics:
        """Get structured evaluation metrics."""
        self.finalize_metrics()
        return self.evaluation

    def reset(self) -> None:
        """Reset all counters and timings."""
        self.counts.clear()
        self.timings.clear()
        self.timing_counts.clear()
        self.evaluation = EvaluationMetrics()
        self._query_times_ms.clear()

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

        sorted_timings = sorted(summary["timings"].items(), key=lambda x: -x[1]["total_seconds"])
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
        sorted_timings = sorted(summary["timings"].items(), key=lambda x: -x[1]["total_seconds"])
        for op, data in sorted_timings:
            total = data["total_seconds"]
            calls = data["call_count"]
            avg = data["avg_ms"]
            print(f"  {op}: {total:.3f}s total, {calls} calls, {avg:.2f}ms avg")

    def _print_rich_evaluation(self, console) -> None:
        """Print evaluation metrics as rich tables."""
        from rich.table import Table

        self.finalize_metrics()
        evaluation = self.evaluation

        # Function metrics
        func = evaluation.function
        if func.name or func.cfg_nodes > 0:
            table = Table(title="Function Metrics", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right", style="green")
            if func.name:
                table.add_row("Function Name", func.name)
            table.add_row("CFG Nodes", str(func.cfg_nodes))
            table.add_row("Basic Blocks", str(func.basic_blocks))
            table.add_row("Parameters", str(func.parameters))
            table.add_row("Local Variables", str(func.local_variables))
            table.add_row("State Variables", str(func.state_variables_accessed))
            table.add_row("Loops", str(func.loops))
            table.add_row("External Calls", str(func.external_calls))
            console.print(table)

        # Analysis convergence metrics
        analysis = evaluation.analysis
        if analysis.worklist_iterations > 0:
            table = Table(title="Analysis Convergence", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right", style="green")
            table.add_row("Worklist Iterations", str(analysis.worklist_iterations))
            table.add_row("Widening Applications", str(analysis.widening_applications))
            table.add_row("Narrowing Applications", str(analysis.narrowing_applications))
            table.add_row("Back Edges Detected", str(analysis.back_edges_detected))
            table.add_row("Fixpoint Reached", "Yes" if analysis.fixpoint_reached else "No")
            console.print(table)

        # Constraint metrics
        constraints = evaluation.constraints
        if constraints.total_constraints > 0:
            table = Table(title="Constraint Statistics", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right", style="green")
            table.add_row("Total Constraints", str(constraints.total_constraints))
            table.add_row("Equality (==)", str(constraints.equality_constraints))
            table.add_row("Inequality (<, >, <=, >=)", str(constraints.inequality_constraints))
            table.add_row("Arithmetic", str(constraints.arithmetic_constraints))
            table.add_row("Overflow Predicates", str(constraints.overflow_predicates))
            table.add_row("Path Constraints", str(constraints.path_constraints))
            table.add_row("256-bit Bitvectors", str(constraints.bitvector_256bit))
            table.add_row("Other Bitvectors", str(constraints.bitvector_other))
            console.print(table)

        # Solver outcome metrics
        solver = evaluation.solver
        total_queries = solver.sat_results + solver.unsat_results
        total_queries += solver.timeout_results + solver.unknown_results
        if total_queries > 0:
            table = Table(title="Solver Performance", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right", style="green")
            table.add_row("SAT Results", str(solver.sat_results))
            table.add_row("UNSAT Results", str(solver.unsat_results))
            table.add_row("Timeout Results", str(solver.timeout_results))
            table.add_row("Unknown Results", str(solver.unknown_results))
            table.add_row("Total Solver Time", f"{solver.total_solver_time_ms:.2f} ms")
            table.add_row("Avg Query Time", f"{solver.avg_query_time_ms:.2f} ms")
            table.add_row("Max Query Time", f"{solver.max_query_time_ms:.2f} ms")
            table.add_row("Min Query Time", f"{solver.min_query_time_ms:.2f} ms")
            console.print(table)

        # Transfer function metrics
        transfer = evaluation.transfer_functions
        total_ops = transfer.operations_handled + transfer.operations_skipped
        if total_ops > 0:
            table = Table(title="Transfer Function Operations", show_header=True)
            table.add_column("Category", style="cyan")
            table.add_column("Count", justify="right", style="green")
            table.add_row("Arithmetic", str(transfer.arithmetic_ops))
            table.add_row("Comparison", str(transfer.comparison_ops))
            table.add_row("Bitwise", str(transfer.bitwise_ops))
            table.add_row("Memory", str(transfer.memory_ops))
            table.add_row("Storage", str(transfer.storage_ops))
            table.add_row("Calls", str(transfer.call_ops))
            table.add_row("Assignment", str(transfer.assignment_ops))
            table.add_row("─" * 20, "─" * 10)
            table.add_row("Handled", str(transfer.operations_handled))
            table.add_row("Skipped", str(transfer.operations_skipped))
            console.print(table)

        # Precision metrics
        precision = evaluation.precision
        if precision.variables_total > 0:
            table = Table(title="Precision Metrics", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right", style="green")
            table.add_row("Total Variables", str(precision.variables_total))
            table.add_row("Precise Bounds", str(precision.variables_with_precise_bounds))
            table.add_row("Full Range", str(precision.variables_with_full_range))
            table.add_row("Precision Ratio", f"{precision.precision_ratio:.2%}")
            table.add_row("Overflow Warnings", str(precision.overflow_warnings))
            table.add_row("Underflow Warnings", str(precision.underflow_warnings))
            console.print(table)

    def _print_text_evaluation(self) -> None:
        """Print evaluation metrics as plain text."""
        self.finalize_metrics()
        evaluation = self.evaluation

        # Function metrics
        func = evaluation.function
        if func.name or func.cfg_nodes > 0:
            print("\nFunction Metrics:")
            if func.name:
                print(f"  Function Name: {func.name}")
            print(f"  CFG Nodes: {func.cfg_nodes}")
            print(f"  Basic Blocks: {func.basic_blocks}")
            print(f"  Parameters: {func.parameters}")
            print(f"  Local Variables: {func.local_variables}")
            print(f"  State Variables: {func.state_variables_accessed}")
            print(f"  Loops: {func.loops}")
            print(f"  External Calls: {func.external_calls}")

        # Analysis convergence
        analysis = evaluation.analysis
        if analysis.worklist_iterations > 0:
            print("\nAnalysis Convergence:")
            print(f"  Worklist Iterations: {analysis.worklist_iterations}")
            print(f"  Widening Applications: {analysis.widening_applications}")
            print(f"  Narrowing Applications: {analysis.narrowing_applications}")
            print(f"  Back Edges Detected: {analysis.back_edges_detected}")
            print(f"  Fixpoint Reached: {'Yes' if analysis.fixpoint_reached else 'No'}")

        # Constraints
        constraints = evaluation.constraints
        if constraints.total_constraints > 0:
            print("\nConstraint Statistics:")
            print(f"  Total Constraints: {constraints.total_constraints}")
            print(f"  Equality (==): {constraints.equality_constraints}")
            print(f"  Inequality (<, >, <=, >=): {constraints.inequality_constraints}")
            print(f"  Arithmetic: {constraints.arithmetic_constraints}")
            print(f"  Overflow Predicates: {constraints.overflow_predicates}")
            print(f"  Path Constraints: {constraints.path_constraints}")
            print(f"  256-bit Bitvectors: {constraints.bitvector_256bit}")
            print(f"  Other Bitvectors: {constraints.bitvector_other}")

        # Solver performance
        solver = evaluation.solver
        total_queries = solver.sat_results + solver.unsat_results
        total_queries += solver.timeout_results + solver.unknown_results
        if total_queries > 0:
            print("\nSolver Performance:")
            print(f"  SAT Results: {solver.sat_results}")
            print(f"  UNSAT Results: {solver.unsat_results}")
            print(f"  Timeout Results: {solver.timeout_results}")
            print(f"  Unknown Results: {solver.unknown_results}")
            print(f"  Total Solver Time: {solver.total_solver_time_ms:.2f} ms")
            print(f"  Avg Query Time: {solver.avg_query_time_ms:.2f} ms")
            print(f"  Max Query Time: {solver.max_query_time_ms:.2f} ms")
            print(f"  Min Query Time: {solver.min_query_time_ms:.2f} ms")

        # Transfer functions
        transfer = evaluation.transfer_functions
        total_ops = transfer.operations_handled + transfer.operations_skipped
        if total_ops > 0:
            print("\nTransfer Function Operations:")
            print(f"  Arithmetic: {transfer.arithmetic_ops}")
            print(f"  Comparison: {transfer.comparison_ops}")
            print(f"  Bitwise: {transfer.bitwise_ops}")
            print(f"  Memory: {transfer.memory_ops}")
            print(f"  Storage: {transfer.storage_ops}")
            print(f"  Calls: {transfer.call_ops}")
            print(f"  Assignment: {transfer.assignment_ops}")
            print("  ---")
            print(f"  Handled: {transfer.operations_handled}")
            print(f"  Skipped: {transfer.operations_skipped}")

        # Precision
        precision = evaluation.precision
        if precision.variables_total > 0:
            print("\nPrecision Metrics:")
            print(f"  Total Variables: {precision.variables_total}")
            print(f"  Precise Bounds: {precision.variables_with_precise_bounds}")
            print(f"  Full Range: {precision.variables_with_full_range}")
            print(f"  Precision Ratio: {precision.precision_ratio:.2%}")
            print(f"  Overflow Warnings: {precision.overflow_warnings}")
            print(f"  Underflow Warnings: {precision.underflow_warnings}")

    def print_summary(self, console=None, include_evaluation: bool = True) -> None:
        """Print a formatted summary of telemetry data.

        Args:
            console: Rich console for formatted output (None for plain text)
            include_evaluation: Whether to include evaluation metrics
        """
        summary = self.get_summary()
        opt_metrics = self.get_optimization_metrics()

        if console:
            if include_evaluation:
                self._print_rich_evaluation(console)
            self._print_rich_optimization(opt_metrics, console)
            self._print_rich_counts(summary, console)
            self._print_rich_timings(summary, console)
        else:
            print("\n=== SMT Solver Telemetry ===")
            if include_evaluation:
                self._print_text_evaluation()
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
