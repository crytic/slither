import argparse
import inspect
import json
import logging
import sys
from typing import List, Any, Type, Dict, Tuple, Union, Sequence, Optional

from crytic_compile import cryticparser


from slither import Slither
from slither.core.declarations import Contract
from slither.exceptions import SlitherException
from slither.utils.colors import red
from slither.utils.output import output_to_json
from slither.tools.upgradeability.checks import all_checks
from slither.tools.upgradeability.checks.abstract_checks import (
    AbstractCheck,
    CheckClassification,
)
from slither.tools.upgradeability.utils.command_line import (
    output_detectors_json,
    output_wiki,
    output_detectors,
    output_to_markdown,
)

logging.basicConfig()
logger: logging.Logger = logging.getLogger("Slither")
logger.setLevel(logging.INFO)


def parse_args(check_classes: List[Type[AbstractCheck]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Slither Upgradeability Checks. For usage information see https://github.com/crytic/slither/wiki/Upgradeability-Checks.",
        usage="slither-check-upgradeability contract.sol ContractName",
    )

    group_checks = parser.add_argument_group("Checks")

    parser.add_argument("contract.sol", help="Codebase to analyze")
    parser.add_argument("ContractName", help="Contract name (logic contract)")

    parser.add_argument("--proxy-name", help="Proxy name")
    parser.add_argument("--proxy-filename", help="Proxy filename (if different)")

    parser.add_argument("--new-contract-name", help="New contract name (if changed)")
    parser.add_argument(
        "--new-contract-filename", help="New implementation filename (if different)"
    )

    parser.add_argument(
        "--json",
        help='Export the results as a JSON file ("--json -" to export to stdout)',
        action="store",
        default=False,
    )

    group_checks.add_argument(
        "--detect",
        help="Comma-separated list of detectors, defaults to all, "
        f"available detectors: {', '.join(d.ARGUMENT for d in check_classes)}",
        action="store",
        dest="detectors_to_run",
        default="all",
    )

    group_checks.add_argument(
        "--list-detectors",
        help="List available detectors",
        action=ListDetectors,
        nargs=0,
        default=False,
    )

    group_checks.add_argument(
        "--exclude",
        help="Comma-separated list of detectors that should be excluded",
        action="store",
        dest="detectors_to_exclude",
        default=None,
    )

    group_checks.add_argument(
        "--exclude-informational",
        help="Exclude informational impact analyses",
        action="store_true",
        default=False,
    )

    group_checks.add_argument(
        "--exclude-low",
        help="Exclude low impact analyses",
        action="store_true",
        default=False,
    )

    group_checks.add_argument(
        "--exclude-medium",
        help="Exclude medium impact analyses",
        action="store_true",
        default=False,
    )

    group_checks.add_argument(
        "--exclude-high",
        help="Exclude high impact analyses",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--markdown-root",
        help="URL for markdown generation",
        action="store",
        default="",
    )

    parser.add_argument(
        "--wiki-detectors", help=argparse.SUPPRESS, action=OutputWiki, default=False
    )

    parser.add_argument(
        "--list-detectors-json",
        help=argparse.SUPPRESS,
        action=ListDetectorsJson,
        nargs=0,
        default=False,
    )

    parser.add_argument("--markdown", help=argparse.SUPPRESS, action=OutputMarkdown, default=False)

    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


###################################################################################
###################################################################################
# region checks
###################################################################################
###################################################################################


def _get_checks() -> List[Type[AbstractCheck]]:
    detectors_ = [getattr(all_checks, name) for name in dir(all_checks)]
    detectors: List[Type[AbstractCheck]] = [
        c for c in detectors_ if inspect.isclass(c) and issubclass(c, AbstractCheck)
    ]
    return detectors


def choose_checks(
    args: argparse.Namespace, all_check_classes: List[Type[AbstractCheck]]
) -> List[Type[AbstractCheck]]:
    detectors_to_run = []
    detectors = {d.ARGUMENT: d for d in all_check_classes}

    if args.detectors_to_run == "all":
        detectors_to_run = all_check_classes
        if args.detectors_to_exclude:
            detectors_excluded = args.detectors_to_exclude.split(",")
            for detector in detectors:
                if detector in detectors_excluded:
                    detectors_to_run.remove(detectors[detector])
    else:
        for detector in args.detectors_to_run.split(","):
            if detector in detectors:
                detectors_to_run.append(detectors[detector])
            else:
                raise Exception(f"Error: {detector} is not a detector")
        detectors_to_run = sorted(detectors_to_run, key=lambda x: x.IMPACT)
        return detectors_to_run

    if args.exclude_informational:
        detectors_to_run = [
            d for d in detectors_to_run if d.IMPACT != CheckClassification.INFORMATIONAL
        ]
    if args.exclude_low:
        detectors_to_run = [d for d in detectors_to_run if d.IMPACT != CheckClassification.LOW]
    if args.exclude_medium:
        detectors_to_run = [d for d in detectors_to_run if d.IMPACT != CheckClassification.MEDIUM]
    if args.exclude_high:
        detectors_to_run = [d for d in detectors_to_run if d.IMPACT != CheckClassification.HIGH]

    # detectors_to_run = sorted(detectors_to_run, key=lambda x: x.IMPACT)
    return detectors_to_run


class ListDetectors(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self, parser: Any, *args: Any, **kwargs: Any
    ) -> None:  # pylint: disable=signature-differs
        checks = _get_checks()
        output_detectors(checks)
        parser.exit()


class ListDetectorsJson(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self, parser: Any, *args: Any, **kwargs: Any
    ) -> None:  # pylint: disable=signature-differs
        checks = _get_checks()
        detector_types_json = output_detectors_json(checks)
        print(json.dumps(detector_types_json))
        parser.exit()


class OutputMarkdown(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self,
        parser: Any,
        args: Any,
        values: Optional[Union[str, Sequence[Any]]],
        option_string: Any = None,
    ) -> None:  # pylint: disable=signature-differs
        checks = _get_checks()
        assert isinstance(values, str)
        output_to_markdown(checks, values)
        parser.exit()


class OutputWiki(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self,
        parser: Any,
        args: Any,
        values: Optional[Union[str, Sequence[Any]]],
        option_string: Any = None,
    ) -> Any:  # pylint: disable=signature-differs
        checks = _get_checks()
        assert isinstance(values, str)
        output_wiki(checks, values)
        parser.exit()


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
def main() -> None:
    json_results: Dict = {
        "proxy-present": False,
        "contract_v2-present": False,
        "detectors": [],
    }

    detectors = _get_checks()
    args = parse_args(detectors)
    detectors_to_run = choose_checks(args, detectors)
    v1_filename = vars(args)["contract.sol"]
    number_detectors_run = 0
    try:
        variable1 = Slither(v1_filename, **vars(args))

        # Analyze logic contract
        v1_name = args.ContractName
        v1_contracts = variable1.get_contract_from_name(v1_name)
        if len(v1_contracts) != 1:
            info = f"Contract {v1_name} not found in {variable1.filename}"
            logger.error(red(info))
            if args.json:
                output_to_json(args.json, str(info), json_results)
            return
        v1_contract = v1_contracts[0]

        detectors_results, number_detectors = _checks_on_contract(detectors_to_run, v1_contract)
        json_results["detectors"] += detectors_results
        number_detectors_run += number_detectors

        # Analyze Proxy
        proxy_contract = None
        if args.proxy_name:
            if args.proxy_filename:
                proxy = Slither(args.proxy_filename, **vars(args))
            else:
                proxy = variable1

            proxy_contracts = proxy.get_contract_from_name(args.proxy_name)
            if len(proxy_contracts) != 1:
                info = f"Proxy {args.proxy_name} not found in {proxy.filename}"
                logger.error(red(info))
                if args.json:
                    output_to_json(args.json, str(info), json_results)
                return
            proxy_contract = proxy_contracts[0]
            json_results["proxy-present"] = True

            detectors_results, number_detectors = _checks_on_contract_and_proxy(
                detectors_to_run, v1_contract, proxy_contract
            )
            json_results["detectors"] += detectors_results
            number_detectors_run += number_detectors
        # Analyze new version
        if args.new_contract_name:
            if args.new_contract_filename:
                variable2 = Slither(args.new_contract_filename, **vars(args))
            else:
                variable2 = variable1

            v2_contracts = variable2.get_contract_from_name(args.new_contract_name)
            if len(v2_contracts) != 1:
                info = (
                    f"New logic contract {args.new_contract_name} not found in {variable2.filename}"
                )
                logger.error(red(info))
                if args.json:
                    output_to_json(args.json, str(info), json_results)
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
        if args.json:
            output_to_json(args.json, None, json_results)

    except SlitherException as slither_exception:
        logger.error(str(slither_exception))
        if args.json:
            output_to_json(args.json, str(slither_exception), json_results)
        return


# endregion
