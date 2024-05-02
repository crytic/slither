import inspect
import json
import logging
from typing import List, Type, Dict, Tuple, Union, Optional, Annotated

import typer

from slither import Slither
from slither.core.declarations import Contract
from slither.exceptions import SlitherException
from slither.utils.colors import red
from slither.utils.output import output_to_json, OutputFormat
from slither.tools.upgradeability.checks import all_checks
from slither.tools.upgradeability.checks.abstract_checks import (
    AbstractCheck,
    CheckClassification,
)
from slither.tools.upgradeability.utils.command_line import (
    output_detectors_json,
    output_wiki,
    output_detectors,
)

from slither.__main__ import app
from slither.utils.command_line import (
    target_type,
    SlitherState,
    SlitherApp,
    GroupWithCrytic,
    MarkdownRoot,
)


upgradeability_app: SlitherApp = SlitherApp()
app.add_typer(upgradeability_app, name="check-upgradeability")


logging.basicConfig()
logger: logging.Logger = logging.getLogger("Slither")
logger.setLevel(logging.INFO)


###################################################################################
###################################################################################
# region checks
###################################################################################
###################################################################################


def list_detectors_json(ctx: typer.Context, value: bool) -> None:
    """Action: list detectors in JSON"""
    if not value or ctx.resilient_parsing:
        return

    checks = _get_checks()
    detector_types_json = output_detectors_json(checks)
    print(json.dumps(detector_types_json))
    raise typer.Exit(code=0)


def _get_checks() -> List[Type[AbstractCheck]]:
    detectors_ = [getattr(all_checks, name) for name in dir(all_checks)]
    detectors: List[Type[AbstractCheck]] = [
        c for c in detectors_ if inspect.isclass(c) and issubclass(c, AbstractCheck)
    ]
    return detectors


def choose_checks(
    arg_checks_to_run: str,
    arg_checks_exclude: str,
    exclude_low: bool = False,
    exclude_medium: bool = False,
    exclude_high: bool = False,
    exclude_informational: bool = False,
    all_check_classes: List[Type[AbstractCheck]] = None,
) -> List[Type[AbstractCheck]]:
    checks_to_run = []

    if all_check_classes is None:
        return []

    checks = {d.ARGUMENT: d for d in all_check_classes}

    if arg_checks_to_run == "all":
        checks_to_run = all_check_classes
        if arg_checks_exclude:
            checks_excluded = arg_checks_exclude.split(",")
            for check in checks:
                if check in checks_excluded:
                    checks_to_run.remove(checks[check])
    else:
        for check in arg_checks_to_run.split(","):
            if check in checks:
                checks_to_run.append(checks[check])
            else:
                raise Exception(f"Error: {check} is not a detector")
        checks_to_run = sorted(checks_to_run, key=lambda x: x.IMPACT)
        return checks_to_run

    if exclude_informational:
        checks_to_run = [d for d in checks_to_run if d.IMPACT != CheckClassification.INFORMATIONAL]
    if exclude_low:
        checks_to_run = [d for d in checks_to_run if d.IMPACT != CheckClassification.LOW]
    if exclude_medium:
        checks_to_run = [d for d in checks_to_run if d.IMPACT != CheckClassification.MEDIUM]
    if exclude_high:
        checks_to_run = [d for d in checks_to_run if d.IMPACT != CheckClassification.HIGH]

    # detectors_to_run = sorted(detectors_to_run, key=lambda x: x.IMPACT)
    return checks_to_run


def list_detectors_action(ctx: typer.Context, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    checks = _get_checks()
    output_detectors(checks)
    raise typer.Exit()


def output_wiki_action(ctx: typer.Context, _: str, value: Union[str, None] = None):
    if ctx.resilient_parsing or value is None:
        return

    checks = _get_checks()
    output_wiki(checks, value)
    raise typer.Exit()


def _run_checks(detectors: List[AbstractCheck]) -> List[Dict]:
    results_ = [d.check() for d in detectors]
    results_ = [r for r in results_ if r]
    results = [item for sublist in results_ for item in sublist]  # flatten
    return results


def _checks_on_contract(
    detectors: List[Type[AbstractCheck]], contract: Contract
) -> Tuple[List[Dict], int]:
    detectors_ = [
        d(logger, contract)
        for d in detectors
        if (not d.REQUIRE_PROXY and not d.REQUIRE_CONTRACT_V2)
    ]
    return _run_checks(detectors_), len(detectors_)


def _checks_on_contract_update(
    detectors: List[Type[AbstractCheck]], contract_v1: Contract, contract_v2: Contract
) -> Tuple[List[Dict], int]:
    detectors_ = [
        d(logger, contract_v1, contract_v2=contract_v2) for d in detectors if d.REQUIRE_CONTRACT_V2
    ]
    return _run_checks(detectors_), len(detectors_)


def _checks_on_contract_and_proxy(
    detectors: List[Type[AbstractCheck]], contract: Contract, proxy: Contract
) -> Tuple[List[Dict], int]:
    detectors_ = [d(logger, contract, proxy=proxy) for d in detectors if d.REQUIRE_PROXY]
    return _run_checks(detectors_), len(detectors_)


# endregion
###################################################################################
###################################################################################
# region Main
###################################################################################
###################################################################################


# pylint: disable=too-many-statements,too-many-branches,too-many-locals
@upgradeability_app.callback(cls=GroupWithCrytic)
def main(
    ctx: typer.Context,
    target: target_type,
    contract_name: Annotated[str, typer.Argument(help="Contract name")],
    proxy_name: Annotated[Optional[str], typer.Option(help="Proxy name")] = None,
    proxy_filename: Annotated[
        Optional[str], typer.Option(help="Proxy filename (if different).")
    ] = None,
    new_contract_name: Annotated[
        Optional[str], typer.Option(help="New contract name (if changed)")
    ] = None,
    new_contract_filename: Annotated[
        Optional[str], typer.Option(help="New implementation filename (if different)")
    ] = None,
    list_json_detector: Annotated[
        Optional[bool],
        typer.Option("--list-detectors-json", callback=list_detectors_json, hidden=True),
    ] = None,
    list_detectors: Annotated[
        Optional[bool],
        typer.Option(
            "--list-detectors",
            help="List available detectors.",
            callback=list_detectors_action,
            rich_help_panel="Checks",
            is_eager=True,
        ),
    ] = None,
    detectors_to_run: Annotated[
        Optional[str],
        typer.Option(
            "--detect",
            help=f"Comma-separated list of detectors. Available detectors: {', '.join(d.ARGUMENT for d in _get_checks())}",
            rich_help_panel="Checks",
        ),
    ] = "all",
    detectors_to_exclude: Annotated[
        Optional[str],
        typer.Option(
            "--exclude",
            help="Comma-separated list of detectors that should be excluded or all.",
            rich_help_panel="Checks",
        ),
    ] = "",
    exclude_informational: Annotated[
        Optional[bool],
        typer.Option(
            "--exclude-informational",
            help="Exclude informational impact analyses.",
            rich_help_panel="Checks",
        ),
    ] = False,
    exclude_low: Annotated[
        Optional[bool],
        typer.Option(
            "--exclude-low",
            help="Exclude low impact analyses.",
            rich_help_panel="Checks",
        ),
    ] = False,
    exclude_medium: Annotated[
        Optional[bool],
        typer.Option(
            "--exclude-medium",
            help="Exclude medium impact analyses.",
            rich_help_panel="Checks",
        ),
    ] = False,
    exclude_high: Annotated[
        Optional[bool],
        typer.Option(
            "--exclude-high",
            help="Exclude high impact analyses.",
            rich_help_panel="Checks",
        ),
    ] = False,
    markdown_root: Annotated[
        Optional[str],
        typer.Option(
            "--markdown-root",
            help="URL for markdown generation.",
            rich_help_panel="Check",
            click_type=MarkdownRoot(),
        ),
    ] = None,
    wiki_detectors: Annotated[
        Optional[str],
        typer.Option(
            help="Print each detectors information that matches the pattern.",
            callback=output_wiki_action,
            rich_help_panel="Check",
        ),
    ] = None,
) -> None:
    """Slither Upgradeability Checks.

    For usage information see https://github.com/crytic/slither/wiki/Upgradeability-Checks.
    """
    json_results: Dict = {
        "proxy-present": False,
        "contract_v2-present": False,
        "detectors": [],
    }

    checks = _get_checks()

    detectors_to_run = choose_checks(
        arg_checks_to_run=detectors_to_run,
        arg_checks_exclude=detectors_to_exclude,
        exclude_low=exclude_low,
        exclude_medium=exclude_medium,
        exclude_high=exclude_high,
        exclude_informational=exclude_informational,
        all_check_classes=checks,
    )

    v1_filename = target.target
    state = ctx.ensure_object(SlitherState)

    number_detectors_run = 0
    try:
        variable1 = Slither(v1_filename, **state)

        # Analyze logic contract
        v1_name = contract_name
        v1_contracts = variable1.get_contract_from_name(v1_name)
        if len(v1_contracts) != 1:
            info = f"Contract {v1_name} not found in {variable1.filename}"
            logger.error(red(info))
            if state.get("output_format") == OutputFormat.JSON:
                output_to_json(state.get("output_file").as_posix(), str(info), json_results)
            return

        v1_contract = v1_contracts[0]

        detectors_results, number_detectors = _checks_on_contract(detectors_to_run, v1_contract)
        json_results["detectors"] += detectors_results
        number_detectors_run += number_detectors

        # Analyze Proxy
        proxy_contract = None
        if proxy_name:
            if proxy_filename:
                proxy = Slither(proxy_filename, **state)
            else:
                proxy = variable1

            proxy_contracts = proxy.get_contract_from_name(proxy_name)
            if len(proxy_contracts) != 1:
                info = f"Proxy {proxy_name} not found in {proxy.filename}"
                logger.error(red(info))
                if state.get("output_format") == OutputFormat.JSON:
                    output_to_json(state.get("output_file").as_posix(), str(info), json_results)
                return
            proxy_contract = proxy_contracts[0]
            json_results["proxy-present"] = True

            detectors_results, number_detectors = _checks_on_contract_and_proxy(
                detectors_to_run, v1_contract, proxy_contract
            )
            json_results["detectors"] += detectors_results
            number_detectors_run += number_detectors
        # Analyze new version
        if new_contract_name:
            if new_contract_filename:
                variable2 = Slither(new_contract_filename, **state)
            else:
                variable2 = variable1

            v2_contracts = variable2.get_contract_from_name(new_contract_name)
            if len(v2_contracts) != 1:
                info = f"New logic contract {new_contract_name} not found in {variable2.filename}"
                logger.error(red(info))
                if state.get("output_format") == OutputFormat.JSON:
                    output_to_json(state.get("output_file").as_posix(), str(info), json_results)
                return
            v2_contract = v2_contracts[0]
            json_results["contract_v2-present"] = True

            if proxy_contract:
                detectors_results, _ = _checks_on_contract_and_proxy(
                    detectors_to_run, v2_contract, proxy_contract
                )

                json_results["detectors"] += detectors_results

            detectors_results, number_detectors = _checks_on_contract_update(
                detectors_to_run, v1_contract, v2_contract
            )
            json_results["detectors"] += detectors_results
            number_detectors_run += number_detectors

            # If there is a V2, we run the contract-only check on the V2
            detectors_results, number_detectors = _checks_on_contract(detectors_to_run, v2_contract)
            json_results["detectors"] += detectors_results
            number_detectors_run += number_detectors

        to_log = f'{len(json_results["detectors"])} findings, {number_detectors_run} detectors run'
        logger.info(to_log)
        if state.get("output_format") == OutputFormat.JSON:
            output_to_json(state.get("output_file").as_posix(), None, json_results)

    except SlitherException as slither_exception:
        logger.error(str(slither_exception))
        if state.get("output_format") == OutputFormat.JSON:
            output_to_json(
                state.get("output_file").as_posix(), str(slither_exception), json_results
            )
        return


# endregion
