import argparse
import cProfile
import enum
import json
import os
import pstats
import re
import logging
import sys
import textwrap
from dataclasses import dataclass
from functools import lru_cache
from importlib import metadata
from pathlib import Path
from typing import Dict, List, Union, Any, Optional, Callable, Sequence, Tuple

import typer.core
from click import Context
from typer.models import CommandFunctionType
from typing_extensions import Annotated

import click
import typer

from crytic_compile import cryticparser
from crytic_compile.cryticparser.defaults import (
    DEFAULTS_FLAG_IN_CONFIG as DEFAULTS_FLAG_IN_CONFIG_CRYTIC_COMPILE,
)
from crytic_compile.platform.etherscan import SUPPORTED_NETWORK

from slither.utils.colors import yellow, red
from slither.utils.output import ZipType

logger = logging.getLogger("Slither")


class SlitherState(dict):
    """Used to keep the internal state of the application."""

    pass


DEFAULT_JSON_OUTPUT_TYPES = ["detectors", "printers"]
JSON_OUTPUT_TYPES = [
    "compilations",
    "console",
    "detectors",
    "printers",
    "list-detectors",
    "list-printers",
]


class FailOnLevel(enum.Enum):
    PEDANTIC = "pedantic"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    NONE = "none"


class GroupWithCrytic(typer.core.TyperGroup):
    def invoke(self, ctx: Context) -> Any:
        if ctx.args or ctx.protected_args:
            # If we have additional parameters to parse with crytic, they will be stored here.
            # We could have a better solution when this issue is solved in Typer
            # https://github.com/tiangolo/typer/issues/119
            crytic_args, remaining_args = handle_crytic_args(
                ctx.protected_args + ctx.args, no_error=True
            )

            # Remove all handled arguments from the context
            ctx.protected_args = [arg for arg in ctx.protected_args if arg in remaining_args]
            ctx.args = [arg for arg in ctx.args if arg in remaining_args]

            if crytic_args:
                state = ctx.ensure_object(SlitherState)
                state.update(crytic_args)

        return super().invoke(ctx)


class CommandWithCrytic(typer.core.TyperCommand):
    """Command that allow crytic compile arguments."""

    def invoke(self, ctx: Context) -> Any:
        """Command invocation

        Before invoking the command, handle any crytic parameters passed on the command line.
        """
        if ctx.args:
            crytic_args, _ = handle_crytic_args(ctx.args)

            if crytic_args:
                state = ctx.ensure_object(SlitherState)
                state.update(crytic_args)

        return super().invoke(ctx)


class SlitherApp(typer.Typer):
    def __init__(self, default_method: Union[None, str] = None, *args, **kwargs) -> None:
        super().__init__(*args, no_args_is_help=True, **kwargs)
        self.default_method: Union[None, str] = default_method

    @property
    @lru_cache  # noqa: B019  # Intentional caching of click app, no memory leak concern
    def click_app(self) -> Union[GroupWithCrytic, click.Command]:
        return typer.main.get_command(self)

    @property
    def app_commands(self) -> Sequence[str]:
        """Return the app registered commands if we have any."""

        try:
            return self.click_app.commands.keys()
        except AttributeError:
            return []

    def command(self, *args, **kwargs) -> Callable[[CommandFunctionType], CommandFunctionType]:
        """Passthrough command to allow extra options.

        This is used to parse crytic compile arguments.
        """
        context_settings = kwargs.get("context_settings", {})
        context_settings.update(
            {
                "ignore_unknown_options": True,
                "allow_extra_args": True,
            }
        )

        return super().command(
            *args, context_settings=context_settings, cls=CommandWithCrytic, **kwargs
        )

    def callback(self, *args, **kwargs) -> Callable[[CommandFunctionType], CommandFunctionType]:
        """A modified version of the callback accepting extra options tailored for Slither usage."""
        context_settings = kwargs.get("context_settings", {})
        context_settings.update(
            {
                "ignore_unknown_options": True,
                "allow_extra_args": True,
            }
        )

        kwargs["context_settings"] = context_settings
        kwargs["invoke_without_command"] = kwargs.get("invoke_without_command", True)

        return super().callback(*args, **kwargs)

    def original_command(
        self, *args, **kwargs
    ) -> Callable[[CommandFunctionType], CommandFunctionType]:
        """Direct wrapper of the original command."""
        return super().command(*args, **kwargs)

    def original_callback(
        self, *args, **kwargs
    ) -> Callable[[CommandFunctionType], CommandFunctionType]:
        """Direct wrapper to the original callback commnand."""
        return super().callback(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        """Overrides Typer command handling.

        We override the calling mechanism here to allow a smooth transition from the previous CLI
        interface to the new sub command based one.
        """

        if self.default_method is not None and not any(
            command in sys.argv for command in self.app_commands
        ):
            main_command_args = []
            other_command_args = []

            take_next: bool = False
            main_args = {option: param for param in self.click_app.params for option in param.opts}

            command_args = sys.argv[1:]
            for idx, arg in enumerate(command_args):
                if take_next:
                    take_next = False
                    continue

                # The help command is not listed in the main_args directly, so we consider it
                # ourselves
                if arg == "--help":
                    main_command_args.append(arg)
                    continue

                if arg in main_args:
                    main_command_args.append(arg)
                    if not main_args[arg].is_flag:
                        main_command_args.append(command_args[idx + 1])
                        take_next = True
                else:
                    other_command_args.append(arg)

            if other_command_args:
                sys.argv = [
                    sys.argv[0],
                    *main_command_args,
                    self.default_method,
                    *other_command_args,
                ]
                logger.info(
                    "Deprecation Notice: Slither CLI has moved to a subcommand based interface. "
                    "This command has been automatically transposed to: %s",
                    " ".join(sys.argv),
                )

        super().__call__(*args, **kwargs)

        return


@click.pass_context
def slither_end_callback(ctx: click.Context, *args, **kwargs) -> None:
    """End execution callback."""

    # If we have asked for the perf object
    ctx.state = ctx.ensure_object(SlitherState)
    perf: Union[cProfile.Profile, None] = ctx.state.get("perf", None)
    if perf is not None:
        perf.disable()
        stats = pstats.Stats(perf).sort_stats("cumtime")
        stats.print_stats()


def format_crytic_help(ctx: typer.Context):
    """"""
    parser = argparse.ArgumentParser()
    cryticparser.init(parser)

    for action_group in parser._action_groups:
        if action_group.title in ("positional arguments", "options"):
            continue

        for action in action_group._group_actions:
            param = click.Option(
                action.option_strings,
                help=action.help,
                hidden=False,  # TODO(dm)
                show_default=False,
            )
            param.rich_help_panel = action_group.title

            ctx.command.params.append(param)


# Those are the flags shared by the command line and the config file
defaults_flag_in_config = {
    "codex": False,
    "codex_contracts": "all",
    "codex_model": "text-davinci-003",
    "codex_temperature": 0,
    "codex_max_tokens": 300,
    "codex_log": False,
    "detectors_to_run": "all",
    "printers_to_run": None,
    "detectors_to_exclude": None,
    "exclude_dependencies": False,
    "exclude_informational": False,
    "exclude_optimization": False,
    "exclude_low": False,
    "exclude_medium": False,
    "exclude_high": False,
    "fail_on": FailOnLevel.PEDANTIC,
    "json": None,
    "sarif": None,
    "json-types": ",".join(DEFAULT_JSON_OUTPUT_TYPES),
    "disable_color": False,
    "filter_paths": None,
    "include_paths": None,
    "generate_patches": False,
    # debug command
    "skip_assembly": False,
    "legacy_ast": False,
    "zip": None,
    "zip_type": ZipType.LZMA,
    "show_ignored_findings": False,
    "no_fail": False,
    "sarif_input": "export.sarif",
    "sarif_triage": "export.sarif.sarifexplorer",
    "triage_database": "slither.db.json",
    **DEFAULTS_FLAG_IN_CONFIG_CRYTIC_COMPILE,
}


def read_config_file(config_file: Union[None, Path]) -> Dict[str, Any]:
    if config_file is None:
        config_path = Path("slither.config.json")
    else:
        config_path = config_file

    state: Dict[str, Any] = defaults_flag_in_config
    if config_path.is_file():
        with config_path.open(encoding="utf-8") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError as exc:
                logger.error(red(f"Impossible to read {config_file}, please check the file {exc}"))

            for key, elem in config.items():
                if key not in defaults_flag_in_config:
                    logger.info(yellow(f"{config_file} has an unknown key: {key} : {elem}"))
                    continue

                state[key] = elem

    elif config_file is not None:
        logger.error(red(f"File {config_file} is not a file or does not exist"))
        logger.error(yellow("Falling back to the default settings..."))

    return state


def version_callback(ctx: typer.Context, value: bool) -> None:
    """Callback called when the --version flag is used."""
    if not value or ctx.resilient_parsing:
        return

    print(metadata.version("slither-analyzer"))
    raise typer.Exit(code=0)


class MarkdownRoot(click.ParamType):
    """Type definition for MarkdownRoot."""

    name = "MarkdownRoot"

    def convert(self, markdown_root: Union[None, str], param, ctx) -> Union[str, None]:
        """Convert and validates the markdown root option"""
        if markdown_root is None or ctx.resilient_parsing:
            return

        # Regex to check whether the markdown_root is a GitHub URL
        match = re.search(
            r"(https://)github.com/([a-zA-Z-]+)([:/][A-Za-z0-9_.-]+[:/]?)([A-Za-z0-9_.-]*)(.*)",
            markdown_root,
        )
        if not match:
            self.fail(f"{markdown_root!r} is invalid.", param, ctx)

        if markdown_root[-1] != "/":
            logger.warning("Appending '/' in markdown_root url for better code referencing")
            markdown_root = markdown_root + "/"

        if not match.group(4):
            logger.warning(
                "Appending 'master/tree/' in markdown_root url for better code referencing"
            )
            markdown_root = markdown_root + "master/tree/"
        elif match.group(4) == "tree":
            logger.warning(
                "Replacing 'tree' with 'blob' in markdown_root url for better code referencing"
            )
            positions = match.span(4)
            markdown_root = f"{markdown_root[: positions[0]]}blob{markdown_root[positions[1] :]}"

        return markdown_root


class CommaSeparatedValueParser(click.ParamType):
    name = "CommaSeparatedValue"

    help = "A comma-separated list of values."

    def convert(self, value: Union[str, None], param, ctx) -> List[str]:
        if value is None or ctx.resilient_parsing:
            return []

        paths = value.split(",")
        return paths


def long_help(ctx: typer.Context, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    format_crytic_help(ctx)
    ctx.get_help()
    raise typer.Exit()


def handle_crytic_args(args: List[str], no_error: bool = False) -> Tuple[Dict[str, str], List[str]]:
    """Handle the crytic arguments passed and not handled by slither."""

    crytic_args = {}
    if args:
        parser = argparse.ArgumentParser(allow_abbrev=False, add_help=False)
        cryticparser.init(parser)

        crytic_args, remaining_args = parser.parse_known_args(args)
        arg_mapping = {key: value for key, value in vars(crytic_args).items()}
        if remaining_args and not no_error:
            msg = "Unknown arguments: %s" % remaining_args
            raise typer.BadParameter(msg)

        return arg_mapping, remaining_args

    return crytic_args, []


@dataclass
class Target:
    target: Union[str, Path]

    HELP: str = textwrap.dedent(
        f"""
    Target can be:

    - *file.sol*: a Solidity file
    
    - *project_directory*: a project directory. 
      See the [documentation](https://github.com/crytic/crytic-compile/#crytic-compile) for the supported 
      platforms.
    
    - *0x..* : a contract address on mainnet
    
    - *NETWORK:0x..*: a contract on a different network.
      Supported networks: {", ".join(x[:-1] for x in SUPPORTED_NETWORK)}
    """
    )


class TargetParam(click.ParamType):
    name = "Target"

    def convert(self, value: Union[str, Path], param, ctx) -> Union[Target, None]:
        if ctx.resilient_parsing:
            return None

        return Target(value)


target_type = Annotated[
    Optional[Target], typer.Argument(..., help=Target.HELP, click_type=TargetParam())
]
