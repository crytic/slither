import logging
import argparse
import sys
from collections import defaultdict

from slither import Slither
from crytic_compile import cryticparser
from slither.exceptions import SlitherException
from slither.utils.json_utils import output_json

from .compare_variables_order import compare_variables_order
from .compare_function_ids import compare_function_ids
from .check_initialization import check_initialization
from .check_variable_initialization import check_variable_initialization
from .constant_checks import constant_conformance_check

logging.basicConfig()
logger = logging.getLogger("Slither-check-upgradeability")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
logger.addHandler(ch)
logger.handlers[0].setFormatter(formatter)
logger.propagate = False

def parse_args():

    parser = argparse.ArgumentParser(description='Slither Upgradeability Checks. For usage information see https://github.com/crytic/slither/wiki/Upgradeability-Checks.',
                                     usage="slither-check-upgradeability contract.sol ContractName")


    parser.add_argument('contract.sol', help='Codebase to analyze')
    parser.add_argument('ContractName', help='Contract name (logic contract)')

    parser.add_argument('--proxy-name', help='Proxy name')
    parser.add_argument('--proxy-filename', help='Proxy filename (if different)')

    parser.add_argument('--new-contract-name', help='New contract name (if changed)')
    parser.add_argument('--new-contract-filename', help='New implementation filename (if different)')

    parser.add_argument('--json',
                        help='Export the results as a JSON file ("--json -" to export to stdout)',
                        action='store',
                        default=False)
    
    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


###################################################################################
###################################################################################
# region
###################################################################################
###################################################################################

def _checks_on_contract(contract, json_results):
    """

    :param contract:
    :param json_results:
    :return:
    """
    json_results['check-initialization'][contract.name] = check_initialization(contract)
    json_results['variable-initialization'][contract.name] = check_variable_initialization(contract)


def _checks_on_contract_update(contract_v1, contract_v2, json_results):
    """

    :param contract_v1:
    :param contract_v2:
    :param json_results:
    :return:
    """
    ret = compare_variables_order(contract_v1, contract_v2)
    json_results['compare-variables-order-implementation'][contract_v1.name][contract_v2.name] = ret

    json_results['constant_conformance'][contract_v1.name][contract_v2.name] = constant_conformance_check(contract_v1,
                                                                                                          contract_v2)


def _checks_on_contract_and_proxy(contract, proxy, json_results, missing_variable_check=True):
    """

    :param contract:
    :param proxy:
    :param json_results:
    :return:
    """
    json_results['compare-function-ids'][contract.name] = compare_function_ids(contract, proxy)
    json_results['compare-variables-order-proxy'][contract.name] = compare_variables_order(contract,
                                                                                           proxy,
                                                                                           missing_variable_check)

# endregion
###################################################################################
###################################################################################
# region Main
###################################################################################
###################################################################################


def main():
    json_results = {
        'check-initialization': defaultdict(dict),
        'variable-initialization': defaultdict(dict),
        'compare-function-ids': defaultdict(dict),
        'compare-variables-order-implementation': defaultdict(dict),
        'compare-variables-order-proxy': defaultdict(dict),
        'constant_conformance': defaultdict(dict),
        'proxy-present': False,
        'contract_v2-present': False
    }

    args = parse_args()

    v1_filename = vars(args)['contract.sol']

    try:
        v1 = Slither(v1_filename, **vars(args))

        # Analyze logic contract
        v1_name = args.ContractName
        v1_contract = v1.get_contract_from_name(v1_name)
        if v1_contract is None:
            info = 'Contract {} not found in {}'.format(v1_name, v1.filename)
            logger.error(info)
            if args.json:
                output_json(args.json, str(info), {"upgradeability-check": json_results})
            return

        _checks_on_contract(v1_contract, json_results)

        # Analyze Proxy
        proxy_contract = None
        if args.proxy_name:
            if args.proxy_filename:
                proxy = Slither(args.proxy_filename, **vars(args))
            else:
                proxy = v1

            proxy_contract = proxy.get_contract_from_name(args.proxy_name)
            if proxy_contract is None:
                info = 'Proxy {} not found in {}'.format(args.proxy_name, proxy.filename)
                logger.error(info)
                if args.json:
                    output_json(args.json, str(info), {"upgradeability-check": json_results})
                return
            json_results['proxy-present'] = True
            _checks_on_contract_and_proxy(v1_contract, proxy_contract, json_results)

        # Analyze new version
        if args.new_contract_name:
            if args.new_contract_filename:
                v2 = Slither(args.new_contract_filename, **vars(args))
            else:
                v2 = v1

            v2_contract = v2.get_contract_from_name(args.new_contract_name)
            if v2_contract is None:
                info = 'New logic contract {} not found in {}'.format(args.new_contract_name, v2.filename)
                logger.error(info)
                if args.json:
                    output_json(args.json, str(info), {"upgradeability-check": json_results})
                return
            json_results['contract_v2-present'] = True

            if proxy_contract:
                _checks_on_contract_and_proxy(v2_contract,
                                              proxy_contract,
                                              json_results,
                                              missing_variable_check=False)

            _checks_on_contract_update(v1_contract, v2_contract, json_results)

        if args.json:
            output_json(args.json, None, {"upgradeability-check": json_results})

    except SlitherException as e:
        logger.error(str(e))
        if args.json:
            output_json(args.json, str(e), {"upgradeability-check": json_results})
        return

# endregion
