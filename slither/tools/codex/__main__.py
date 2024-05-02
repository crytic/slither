import logging
from typing import Annotated, Optional

import typer

from slither import Slither
from slither.__main__ import app
from slither.utils.output import format_output
from slither.utils.command_line import (
    target_type,
    SlitherState,
    SlitherApp,
    GroupWithCrytic,
    defaults_flag_in_config,
)
from slither.tools.codex.utils import openai_module
from slither.tools.codex.documentation import _handle_compilation_unit
from slither.tools.codex.detector import Codex


logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

logger = logging.getLogger("Slither-demo")


codex_app = SlitherApp(help="Codex integration.")
app.add_typer(codex_app, name="codex")


@codex_app.command()
def documentation(
    ctx: typer.Context,
    target: target_type,
    overwrite: Annotated[bool, typer.Option(help="Overwrite the files (be careful).")] = False,
    force_answer_parsing: Annotated[
        bool,
        typer.Option(
            help="Apply heuristics to better parse codex output (might lead to incorrect results)."
        ),
    ] = False,
    include_tests: Annotated[bool, typer.Option(help="Include the tests.")] = False,
    retry: Annotated[
        int,
        typer.Option(help="Retry failed query. Each retry increases the temperature by 0.1"),
    ] = 1,
):
    """Auto-generate NatSpec documentation for every function using OpenAI Codex."""

    state = ctx.ensure_object(SlitherState)
    logger.info("This tool is a WIP, use it with cautious")
    logger.info("Be aware of OpenAI ToS: https://openai.com/api/policies/terms/")
    slither = Slither(target.target, **state)

    try:
        for compilation_unit in slither.compilation_units:
            _handle_compilation_unit(
                slither,
                compilation_unit,
                overwrite,
                force_answer_parsing,
                retry,
                include_tests,
            )
    except ImportError:
        pass


@codex_app.command()
def detect(
    ctx: typer.Context,
    target: target_type,
):
    state = ctx.ensure_object(SlitherState)
    print(f"{state['codex']=}")
    slither = Slither(target.target, **state)

    slither.register_detector(Codex)

    print(len(slither.detectors))

    results = slither.run_detectors()
    detector_results = [x for x in results if x]  # remove empty results

    format_output(
        state.get("output_format"),
        state.get("output_file"),
        [slither],
        detector_results,
        [],
        "",
        runned_detectors=[Codex],
    )


@codex_app.callback(cls=GroupWithCrytic)
def codex_callback(
    ctx: typer.Context,
    api_key: Annotated[
        str, typer.Option("--api-key", help="Open API Key", envvar="OPENAI_API_KEY")
    ],
    codex_log: Annotated[
        bool, typer.Option("--codex-log", help="Log codex queries (in crytic_export/codex/).")
    ] = False,
    codex_contracts: Annotated[
        str,
        typer.Option(
            "--codex-contracts", help="Comma separated list of contracts to submit to OpenAI Codex."
        ),
    ] = defaults_flag_in_config["codex_contracts"],
    codex_model: Annotated[
        str,
        typer.Option("--codex-model", help="Name of the Codex model to use (affects pricing)."),
    ] = defaults_flag_in_config["codex_model"],
    codex_temperature: Annotated[
        int,
        typer.Option(
            "--codex-temperature",
            help="Temperature to use with Codex.  Lower number indicates a more precise answer "
            "while higher numbers return more creative answers.",
        ),
    ] = defaults_flag_in_config["codex_temperature"],
    codex_max_tokens: Annotated[
        int,
        typer.Option(
            "--codex-max-tokens",
            help="Maximum amount of tokens to use on the response. This number plus the size of "
            "the prompt can be no larger than the limit.",
        ),
    ] = defaults_flag_in_config["codex_max_tokens"],
    codex_organization: Annotated[
        Optional[str],
        typer.Option("--codex-organization", help="Codex organization."),
    ] = None,
):
    """Codex (https://beta.openai.com/docs/guides/code)."""

    if openai_module(api_key) is None:
        raise typer.Exit(code=1)

    state = ctx.ensure_object(SlitherState)
    state.update(
        {
            "codex_log": codex_log,
            "codex_organization": codex_organization,
            "codex_model": codex_model,
            "codex_temperature": codex_temperature,
            "codex_max_tokens": codex_max_tokens,
            "codex_contracts": codex_contracts,
            "codex": True,
        }
    )


if __name__ == "__main__":
    codex_app()
