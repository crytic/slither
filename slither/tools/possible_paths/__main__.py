import logging
from typing import Annotated, List

import typer

# Configure logging before slither imports to suppress CryticCompile INFO messages
logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)
logging.getLogger("CryticCompile").setLevel(logging.WARNING)

from slither import Slither
from slither.core.declarations import FunctionContract
from slither.utils.colors import red
from slither.tools.possible_paths.possible_paths import (
    find_target_paths,
    resolve_functions,
    ResolveFunctionException,
)

from slither.__main__ import app
from slither.utils.command_line import target_type, SlitherState, SlitherApp, GroupWithCrytic

possible_paths_app: SlitherApp = SlitherApp()
app.add_typer(possible_paths_app, name="find-paths")


@possible_paths_app.callback(cls=GroupWithCrytic)
def main_callback(
    ctx: typer.Context,
    target: target_type,
    functions: Annotated[
        List[str],
        typer.Argument(
            help="Function to analyze. Should be noted as contract.function. Can be repeated."
        ),
    ],
) -> None:
    """Find the possible paths."""
    state = ctx.ensure_object(SlitherState)
    slither = Slither(target.target, **state)

    try:
        targets = resolve_functions(slither, functions)
    except ResolveFunctionException as resolve_function:
        print(red(resolve_function))
        raise typer.Exit(1)

    # Print out all target functions.
    print("Target functions:")
    for target in targets:
        if isinstance(target, FunctionContract):
            print(f"- {target.contract_declarer.name}.{target.full_name}")
        else:
            pass
            # TODO implement me
    print("\n")

    # Obtain all paths which reach the target functions.
    reaching_paths = find_target_paths(slither, targets)
    reaching_functions = {y for x in reaching_paths for y in x if y not in targets}

    # Print out all function names which can reach the targets.
    print("The following functions reach the specified targets:")
    for function_desc in sorted([f"{f.canonical_name}" for f in reaching_functions]):
        print(f"- {function_desc}")
    print("\n")

    # Format all function paths.
    reaching_paths_str = [
        " -> ".join([f"{f.canonical_name}" for f in reaching_path])
        for reaching_path in reaching_paths
    ]

    # Print a sorted list of all function paths which can reach the targets.
    print("The following paths reach the specified targets:")
    for reaching_path in sorted(reaching_paths_str):
        print(f"{reaching_path}\n")

    raise typer.Exit(0)


def main():
    """Entry point for the slither-find-paths CLI."""
    possible_paths_app()


if __name__ == "__main__":
    main()
