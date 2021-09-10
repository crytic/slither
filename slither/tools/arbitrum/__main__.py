import argparse
import inspect
import json
import logging
import sys
from typing import List

from crytic_compile import cryticparser

from slither import Slither
from slither.tools.arbitrum.checks import all_checks
from slither.tools.arbitrum.checks.abstract_checks import AbstractCheck
from slither.tools.arbitrum.utils.command_line import (
    output_detectors_json,
    output_wiki,
    output_detectors,
    output_to_markdown,
)

logging.basicConfig()
logger: logging.Logger = logging.getLogger("Slither")
logger.setLevel(logging.INFO)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Slither Arbitrum Checks. For usage information see https://github.com/crytic/slither/wiki/Arbitrum-Checks.",
        usage="slither-check-arbitrum [project]]",
    )

    parser.add_argument("project", help="Codebase to analyze")

    parser.add_argument(
        "--list-detectors",
        help="List available detectors",
        action=ListDetectors,
        nargs=0,
        default=False,
    )

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


def _get_checks() -> List:
    detectors = [getattr(all_checks, name) for name in dir(all_checks)]
    detectors = [c for c in detectors if inspect.isclass(c) and issubclass(c, AbstractCheck)]
    return detectors


class ListDetectors(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, *args, **kwargs) -> None:  # pylint: disable=signature-differs
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

    args = parse_args()

    slither = Slither(vars(args)["project"], **vars(args))

    detectors = _get_checks()

    for compilation_unit in slither.compilation_units:
        _run_checks([d(logger, compilation_unit) for d in detectors])


# endregion
