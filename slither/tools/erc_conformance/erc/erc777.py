import logging
from collections import defaultdict
from slither.utils.erc import ERC777
from .ercs import generic_erc_checks
from slither.exceptions import SlitherException

logger = logging.getLogger("Slither-conformance")

def check_erc777(slither, contract_name):

    contract = slither.get_contract_from_name(contract_name)

    if not contract:
        raise SlitherException(f'{contract_name} not found')

    signatures = generic_erc_checks(contract, ERC777)

    ret = defaultdict(dict)

    ret['erc777'] = {
        "signatures": signatures
    }

    return ret

