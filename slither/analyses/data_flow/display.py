"""Display and formatting functions for data flow analysis output."""

from typing import Dict, List, TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from slither.analyses.data_flow.models import ContractTestResult

# Shared console instance
console = Console()


def abbreviate_variable_name(var_name: str, max_length: int = 60) -> str:
    """
    Abbreviate variable names to prevent truncation in table output.

    Handles names like:
    - Contract.function().variable|variable_SSA
    - Contract.function().word_functionName_asm_0|word_functionName_asm_0_0

    Strategy:
    1. Keep contract and function names but abbreviate if needed
    2. Abbreviate long variable names (especially assembly vars)
    3. Preserve SSA suffix information
    """
    if len(var_name) <= max_length:
        return var_name

    # Split on pipe to separate prefix from SSA suffix
    if "|" in var_name:
        prefix, ssa_suffix = var_name.rsplit("|", 1)
    else:
        prefix = var_name
        ssa_suffix = ""

    # Abbreviate common patterns in the prefix
    # Replace long assembly variable patterns
    prefix = prefix.replace("_asm_", "_a_")

    # If prefix contains function call pattern like "Contract.function().var"
    if "()." in prefix:
        parts = prefix.split("().", 1)
        if len(parts) == 2:
            contract_func = parts[0]  # "Contract.function"
            var_part = parts[1]  # "variable" or "word_functionName_a_0"

            # Extract function name from contract_func for abbreviation
            func_name = ""
            if "." in contract_func:
                func_name = contract_func.rsplit(".", 1)[1]

            # Abbreviate long variable names
            # For patterns like "word_readFirstThreeBytes_a_0", shorten significantly
            if var_part.startswith("word_") and len(var_part) > 12:
                remaining = var_part[5:]  # Remove "word_"
                if "_a_" in remaining:
                    func_part, rest = remaining.split("_a_", 1)
                    # If function name is repeated in variable, abbreviate it
                    if func_name and func_part.startswith(func_name):
                        # Function name is repeated, use very short abbrev
                        func_abbrev = func_name[:3] if len(func_name) > 3 else func_name
                        var_part = f"w_{func_abbrev}_a_{rest}"
                    elif func_part:
                        # Take first 3-4 characters of function name
                        func_abbrev = func_part[:4] if len(func_part) > 4 else func_part
                        var_part = f"w_{func_abbrev}_a_{rest}"
                else:
                    # Just truncate if no _a_ pattern
                    var_part = f"w_{remaining[:8]}" if len(remaining) > 8 else f"w_{remaining}"

            # Similar for "ptr_" pattern
            elif var_part.startswith("ptr_") and len(var_part) > 12:
                remaining = var_part[4:]  # Remove "ptr_"
                if "_a_" in remaining:
                    func_part, rest = remaining.split("_a_", 1)
                    # If function name is repeated in variable, abbreviate it
                    if func_name and func_part.startswith(func_name):
                        func_abbrev = func_name[:3] if len(func_name) > 3 else func_name
                        var_part = f"p_{func_abbrev}_a_{rest}"
                    elif func_part:
                        func_abbrev = func_part[:4] if len(func_part) > 4 else func_part
                        var_part = f"p_{func_abbrev}_a_{rest}"
                else:
                    var_part = f"p_{remaining[:8]}" if len(remaining) > 8 else f"p_{remaining}"

            # Keep SSA suffix unchanged - don't abbreviate anything after |

            # Abbreviate contract.function if still too long
            if "." in contract_func:
                contract, func = contract_func.rsplit(".", 1)
                # Abbreviate function name more aggressively
                if len(func) > 10:
                    # Take first 6-8 chars of function name
                    func_abbrev = func[:8] + ".." if len(func) > 8 else func
                    contract_func = f"{contract}.{func_abbrev}"
                # Also abbreviate contract if very long
                elif len(contract) > 15:
                    contract = contract[:12] + ".."
                    contract_func = f"{contract}.{func}"

            prefix = f"{contract_func}().{var_part}"

    # Reconstruct the name
    if ssa_suffix:
        result = f"{prefix}|{ssa_suffix}"
    else:
        result = prefix

    # Final check: if still too long, truncate intelligently
    # Always preserve everything after | (SSA suffix)
    if len(result) > max_length:
        if "|" in result:
            prefix_part, ssa_part = result.rsplit("|", 1)
            # Calculate available space for prefix (leave room for | and SSA suffix)
            available = max_length - len(ssa_part) - 1  # -1 for the |
            if available > 10:
                # Truncate prefix but keep SSA suffix intact
                prefix_part = prefix_part[:available] + ".."
                result = f"{prefix_part}|{ssa_part}"
            else:
                # If SSA suffix itself is too long, we still keep it but truncate prefix minimally
                # This shouldn't happen often, but handle it gracefully
                prefix_part = prefix_part[: max(10, max_length - len(ssa_part) - 1)]
                result = f"{prefix_part}|{ssa_part}"
        else:
            # No pipe, just truncate normally
            result = result[: max_length - 3] + "..."

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

        # Show function details
        for func_name, func_test in contract_test.function_results.items():
            if func_test.passed:
                console.print(
                    f"  [green]V[/green] {contract_test.contract_name}.{func_name} - All variables correct"
                )
            else:
                console.print(
                    f"  [red]X[/red] {contract_test.contract_name}.{func_name} - Variable mismatch"
                )

                # Show mismatches
                for comparison in func_test.comparisons:
                    if not comparison.passed:
                        console.print(f"    [yellow]Variable:[/yellow] {comparison.variable_name}")
                        if comparison.expected_range != comparison.actual_range:
                            console.print(
                                f"      Expected range: [cyan]{comparison.expected_range}[/cyan]"
                            )
                            console.print(
                                f"      Got range:      [red]{comparison.actual_range}[/red]"
                            )
                        if comparison.expected_overflow != comparison.actual_overflow:
                            console.print(
                                f"      Expected overflow: [cyan]{comparison.expected_overflow}[/cyan]"
                            )
                            console.print(
                                f"      Got overflow:      [red]{comparison.actual_overflow}[/red]"
                            )

                # Show missing variables
                for missing in func_test.missing_expected:
                    console.print(f"    [red]Missing expected variable:[/red] {missing}")

                # Show unexpected variables (informational)
                if verbose and func_test.unexpected_vars:
                    for unexpected in func_test.unexpected_vars:
                        console.print(f"    [dim]Unexpected variable:[/dim] {unexpected}")


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
