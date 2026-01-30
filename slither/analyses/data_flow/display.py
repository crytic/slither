"""Display and formatting functions for data flow analysis output."""

from typing import Dict, List, TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from slither.analyses.data_flow.models import ContractTestResult

# Shared console instance
console = Console()


def _abbreviate_asm_pattern(var_part: str, func_name: str, prefix: str) -> str:
    """Abbreviate word_ or ptr_ assembly variable patterns."""
    remaining = var_part[len(prefix):]  # Remove prefix (word_ or ptr_)
    short_prefix = "w_" if prefix == "word_" else "p_"

    if "_a_" in remaining:
        func_part, rest = remaining.split("_a_", 1)
        if func_name and func_part.startswith(func_name):
            func_abbrev = func_name[:3] if len(func_name) > 3 else func_name
        elif func_part:
            func_abbrev = func_part[:4] if len(func_part) > 4 else func_part
        else:
            return f"{short_prefix}{remaining[:8]}"
        return f"{short_prefix}{func_abbrev}_a_{rest}"

    return f"{short_prefix}{remaining[:8]}" if len(remaining) > 8 else f"{short_prefix}{remaining}"


def _abbreviate_contract_func(contract_func: str) -> str:
    """Abbreviate contract.function pattern if too long."""
    if "." not in contract_func:
        return contract_func

    contract, func = contract_func.rsplit(".", 1)
    if len(func) > 10:
        func_abbrev = func[:8] + ".." if len(func) > 8 else func
        return f"{contract}.{func_abbrev}"
    if len(contract) > 15:
        return f"{contract[:12]}..{func}"
    return contract_func


def _truncate_with_ssa(result: str, max_length: int) -> str:
    """Truncate result while preserving SSA suffix after pipe."""
    if "|" in result:
        prefix_part, ssa_part = result.rsplit("|", 1)
        available = max_length - len(ssa_part) - 1
        if available > 10:
            prefix_part = prefix_part[:available] + ".."
        else:
            prefix_part = prefix_part[: max(10, max_length - len(ssa_part) - 1)]
        return f"{prefix_part}|{ssa_part}"
    return result[: max_length - 3] + "..."


def abbreviate_variable_name(var_name: str, max_length: int = 60) -> str:
    """Abbreviate variable names to prevent truncation in table output."""
    if len(var_name) <= max_length:
        return var_name

    # Split on pipe to separate prefix from SSA suffix
    if "|" in var_name:
        prefix, ssa_suffix = var_name.rsplit("|", 1)
    else:
        prefix, ssa_suffix = var_name, ""

    # Replace long assembly variable patterns
    prefix = prefix.replace("_asm_", "_a_")

    # Handle function call pattern like "Contract.function().var"
    if "()." in prefix:
        parts = prefix.split("().", 1)
        if len(parts) == 2:
            contract_func, var_part = parts
            func_name = contract_func.rsplit(".", 1)[1] if "." in contract_func else ""

            # Abbreviate word_ and ptr_ patterns
            if var_part.startswith("word_") and len(var_part) > 12:
                var_part = _abbreviate_asm_pattern(var_part, func_name, "word_")
            elif var_part.startswith("ptr_") and len(var_part) > 12:
                var_part = _abbreviate_asm_pattern(var_part, func_name, "ptr_")

            contract_func = _abbreviate_contract_func(contract_func)
            prefix = f"{contract_func}().{var_part}"

    # Reconstruct with SSA suffix
    result = f"{prefix}|{ssa_suffix}" if ssa_suffix else prefix

    # Final truncation if still too long
    if len(result) > max_length:
        result = _truncate_with_ssa(result, max_length)

    return result


def display_variable_ranges_table(variable_results: List[Dict]) -> None:
    """Display variable ranges in a formatted rich table."""
    if not variable_results:
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Variable", style="bold", justify="left")
    table.add_column("Range", justify="left")
    table.add_column("Overflow", justify="left")
    table.add_column("Overflow Amount", justify="left")

    for result in variable_results:
        var_name = result["name"]
        # Abbreviate long variable names to prevent truncation
        abbreviated_name = abbreviate_variable_name(var_name)
        min_val = result["min"]
        max_val = result["max"]

        has_overflow = min_val.get("overflow", False) or max_val.get("overflow", False)
        is_wrapped = min_val["value"] > max_val["value"]

        if is_wrapped:
            range_str = f"[{max_val['value']}, {min_val['value']}] (wrapped)"
        else:
            range_str = f"[{min_val['value']}, {max_val['value']}]"

        range_style = "red" if has_overflow else "white"

        if has_overflow:
            overflow_str = "X YES"
            overflow_style = "red bold"
            min_overflow = min_val.get("overflow_amount", 0)
            max_overflow = max_val.get("overflow_amount", 0)
            if min_val.get("overflow", False) and max_val.get("overflow", False):
                amount_str = f"min: {min_overflow:+d}, max: {max_overflow:+d}"
            elif min_val.get("overflow", False):
                amount_str = f"min: {min_overflow:+d}"
            else:
                amount_str = f"max: {max_overflow:+d}"
        else:
            overflow_str = "V NO"
            overflow_style = "white"
            amount_str = "-"

        table.add_row(
            abbreviated_name,
            f"[{range_style}]{range_str}[/{range_style}]",
            f"[{overflow_style}]{overflow_str}[/{overflow_style}]",
            f"[{overflow_style}]{amount_str}[/{overflow_style}]",
        )

    console.print(table)


def display_test_results(results: List["ContractTestResult"], verbose: bool) -> None:
    """Display test results with rich formatting."""
    for contract_test in results:
        _display_contract_summary(contract_test)
        _display_function_results(contract_test, verbose)


def _display_contract_summary(contract_test: "ContractTestResult") -> None:
    """Display contract-level test summary."""
    passed_funcs = sum(1 for f in contract_test.function_results.values() if f.passed)
    total_funcs = len(contract_test.function_results)

    if contract_test.passed:
        console.print(
            f"[bold green]V[/bold green] {contract_test.contract_file} - "
            f"[green]PASSED[/green] ({passed_funcs}/{total_funcs} functions)"
        )
    else:
        console.print(
            f"[bold red]X[/bold red] {contract_test.contract_file} - "
            f"[red]FAILED[/red] ({passed_funcs}/{total_funcs} functions)"
        )


def _display_function_results(contract_test: "ContractTestResult", verbose: bool) -> None:
    """Display function-level test results."""
    for func_name, func_test in contract_test.function_results.items():
        cname = contract_test.contract_name
        if func_test.passed:
            console.print(f"  [green]V[/green] {cname}.{func_name} - All vars correct")
        else:
            console.print(f"  [red]X[/red] {cname}.{func_name} - Variable mismatch")
            _display_function_failures(func_test, verbose)


def _display_function_failures(func_test, verbose: bool) -> None:
    """Display failures for a single function."""
    for comparison in func_test.comparisons:
        if not comparison.passed:
            _display_comparison_failure(comparison)

    for missing in func_test.missing_expected:
        console.print(f"    [red]Missing expected variable:[/red] {missing}")

    if verbose and func_test.unexpected_vars:
        for unexpected in func_test.unexpected_vars:
            console.print(f"    [dim]Unexpected variable:[/dim] {unexpected}")


def _display_comparison_failure(comparison) -> None:
    """Display a single comparison failure."""
    console.print(f"    [yellow]Variable:[/yellow] {comparison.variable_name}")
    if comparison.expected_range != comparison.actual_range:
        console.print(f"      Expected range: [cyan]{comparison.expected_range}[/cyan]")
        console.print(f"      Got range:      [red]{comparison.actual_range}[/red]")
    if comparison.expected_overflow != comparison.actual_overflow:
        console.print(f"      Expected overflow: [cyan]{comparison.expected_overflow}[/cyan]")
        console.print(f"      Got overflow:      [red]{comparison.actual_overflow}[/red]")


def display_safety_violations(violations: List) -> None:
    """Display detected safety violations in a formatted panel."""
    if not violations:
        return

    console.print("\n[bold red]" + "=" * 60 + "[/bold red]")
    console.print("[bold red]WARNING: SAFETY VIOLATIONS DETECTED[/bold red]")
    console.print("[bold red]" + "=" * 60 + "[/bold red]\n")

    for i, violation in enumerate(violations, 1):
        severity_style = "red bold" if violation.severity == "CRITICAL" else "yellow bold"
        console.print(
            f"[{severity_style}]#{i} [{violation.severity}] "
            f"{violation.violation_type.value.upper()}[/{severity_style}]"
        )
        console.print(f"  [white]{violation.message}[/white]")

        if violation.write_location_range:
            min_val, max_val = violation.write_location_range
            console.print(
                f"  [cyan]Write location '{violation.write_location_name}' range:[/cyan] "
                f"[{min_val}, {max_val}]"
            )

        if violation.base_pointer_range and violation.base_pointer_name:
            min_val, max_val = violation.base_pointer_range
            console.print(
                f"  [cyan]Base pointer '{violation.base_pointer_name}' range:[/cyan] "
                f"[{min_val}, {max_val}]"
            )

        if violation.recommendation:
            console.print(f"  [green]Recommendation:[/green] {violation.recommendation}")

        console.print()

    console.print("[bold red]" + "=" * 60 + "[/bold red]\n")
