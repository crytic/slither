import logging
from pathlib import Path
from typing import List

from slither.core.declarations import Contract
from slither.tools.properties.addresses.address import Addresses
from slither.tools.properties.platforms.truffle import generate_migration, generate_unit_test
from slither.tools.properties.properties.ercs.erc20.properties.initialization import ERC20_CONFIG
from slither.tools.properties.properties.properties import Property

logger = logging.getLogger("Slither")


def generate_truffle_test(
    contract: Contract, type_property: str, unit_tests: List[Property], addresses: Addresses
) -> str:
    test_contract = f"Test{contract.name}{type_property}"
    filename_init = f"Initialization{test_contract}.js"
    filename = f"{test_contract}.js"

    output_dir = Path(contract.slither.crytic_compile.target)

    generate_migration(test_contract, output_dir, addresses.owner)

    generate_unit_test(
        test_contract,
        filename_init,
        ERC20_CONFIG,
        output_dir,
        addresses,
        f"Check the constructor of {test_contract}",
    )

    generate_unit_test(
        test_contract, filename, unit_tests, output_dir, addresses,
    )

    log_info = "\n"
    log_info += "To run the unit tests:\n"
    log_info += f"\ttruffle test {Path(output_dir, 'test', 'crytic', filename_init)}\n"
    log_info += f"\ttruffle test {Path(output_dir, 'test', 'crytic', filename)}\n"
    return log_info
