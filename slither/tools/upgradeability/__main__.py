import argparse
import inspect
import json
import logging
import sys

from crytic_compile import cryticparser

from slither import Slither
from slither.exceptions import SlitherException
from slither.utils.colors import red
from slither.utils.output import output_to_json
from slither.tools.upgradeability.checks import all_checks
from slither.tools.upgradeability.checks.abstract_checks import AbstractCheck
from slither.tools.upgradeability.utils.command_line import (
    output_detectors_json,
    output_wiki,
    output_detectors,
    output_to_markdown,
)

logging.basicConfig()
logger = logging.getLogger("Slither")
logger.setLevel(logging.INFO)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Slither Upgradeability Checks. For usage information see https://github.com/crytic/slither/wiki/Upgradeability-Checks.",
        usage="slither-check-upgradeability contract.sol ContractName",
    )

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

    parser.add_argument(
        "--list-detectors",
        help="List available detectors",
        action=ListDetectors,
        nargs=0,
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


def _get_checks():
    detectors = [getattr(all_checks, name) for name in dir(all_checks)]
    detectors = [c for c in detectors if inspect.isclass(c) and issubclass(c, AbstractCheck)]
    return detectors


class ListDetectors(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, *args, **kwargs):  # pylint: disable=signature-differs
        checks = _get_checks()
        output_detectors(checks)
        parser.exit()


class ListDetectorsJson(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, *args, **kwargs):  # pylint: disable=signature-differs
        checks = _get_checks()
        detector_types_json = output_detectors_json(checks)
        print(json.dumps(detector_types_json))
        parser.exit()


class OutputMarkdown(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self, parser, args, values, option_string=None
    ):  # pylint: disable=signature-differs
        checks = _get_checks()
        output_to_markdown(checks, values)
        parser.exit()


class OutputWiki(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(
        self, parser, args, values, option_string=None
    ):  # pylint: disable=signature-differs
        checks = _get_checks()
        output_wiki(checks, values)
        parser.exit()


def _run_checks(detectors):
    results = [d.check() for d in detectors]
    results = [r for r in results if r]
    results = [item for sublist in results for item in sublist]  # flatten
    return results


def _checks_on_contract(detectors, contract):
    detectors = [
        d(logger, contract)
        for d in detectors
        if (not d.REQUIRE_PROXY and not d.REQUIRE_CONTRACT_V2)
    ]
    return _run_checks(detectors), len(detectors)


def _checks_on_contract_update(detectors, contract_v1, contract_v2):
    detectors = [
        d(logger, contract_v1, contract_v2=contract_v2) for d in detectors if d.REQUIRE_CONTRACT_V2
    ]
    return _run_checks(detectors), len(detectors)


def _checks_on_contract_and_proxy(detectors, contract, proxy):
    detectors = [d(logger, contract, proxy=proxy) for d in detectors if d.REQUIRE_PROXY]
    return _run_checks(detectors), len(detectors)


# endregion
###################################################################################
###################################################################################
# region Main
###################################################################################
###################################################################################

# pylint: disable=too-many-statements,too-many-branches,too-many-locals
def main():
    json_results = {
        "proxy-present": False,
        "contract_v2-present": False,
        "detectors": [],
    }

    args = parse_args()

    v1_filename = vars(args)["contract.sol"]
    number_detectors_run = 0
    detectors = _get_checks()
    try:
        variable1 = Slither(v1_filename, **vars(args))

        # Analyze logic contract
        v1_name = args.ContractName
        v1_contract = variable1.get_contract_from_name(v1_name)
        if v1_contract is None:
            info = "Contract {} not found in {}".format(v1_name, variable1.filename)
            logger.error(red(info))
            if args.json:
                output_to_json(args.json, str(info), json_results)
            return

        detectors_results, number_detectors = _checks_on_contract(detectors, v1_contract)
        json_results["detectors"] += detectors_results
        number_detectors_run += number_detectors

        # Analyze Proxy
        proxy_contract = None
        if args.proxy_name:
            if args.proxy_filename:
                proxy = Slither(args.proxy_filename, **vars(args))
            else:
                proxy = variable1

            proxy_contract = proxy.get_contract_from_name(args.proxy_name)
            if proxy_contract is None:
                info = "Proxy {} not found in {}".format(args.proxy_name, proxy.filename)
                logger.error(red(info))
                if args.json:
                    output_to_json(args.json, str(info), json_results)
                return
            json_results["proxy-present"] = True

            detectors_results, number_detectors = _checks_on_contract_and_proxy(
                detectors, v1_contract, proxy_contract
            )
            json_results["detectors"] += detectors_results
            number_detectors_run += number_detectors
        # Analyze new version
        if args.new_contract_name:
            if args.new_contract_filename:
                variable2 = Slither(args.new_contract_filename, **vars(args))
            else:
                variable2 = variable1

            v2_contract = variable2.get_contract_from_name(args.new_contract_name)
            if v2_contract is None:
                info = "New logic contract {} not found in {}".format(
                    args.new_contract_name, variable2.filename
                )
                logger.error(red(info))
                if args.json:
                    output_to_json(args.json, str(info), json_results)
                return
            json_results["contract_v2-present"] = True

            if proxy_contract:
                detectors_results, _ = _checks_on_contract_and_proxy(
                    detectors, v2_contract, proxy_contract
                )

                json_results["detectors"] += detectors_results

            detectors_results, number_detectors = _checks_on_contract_update(
                detectors, v1_contract, v2_contract
            )
            json_results["detectors"] += detectors_results
            number_detectors_run += number_detectors

            # If there is a V2, we run the contract-only check on the V2
            detectors_results, _ = _checks_on_contract(detectors, v2_contract)
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
