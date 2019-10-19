import logging
from collections import defaultdict
from slither.utils.erc import ERC721
from .ercs import generic_erc_checks
from slither.exceptions import SlitherException

logger = logging.getLogger("Slither-conformance")

def check_erc721(slither, contract_name):

    contract = slither.get_contract_from_name(contract_name)

    if not contract:
        raise SlitherException(f'{contract_name} not found')

    signatures = generic_erc_checks(contract, ERC721)

    ret = defaultdict(dict)

    ret['erc721'] = {
        "signatures": signatures
    }

    return ret

