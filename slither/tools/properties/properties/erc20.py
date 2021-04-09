import logging
from collections import namedtuple
from pathlib import Path
from typing import Tuple, List

from crytic_compile.platform.abstract_platform import AbstractPlatform
from crytic_compile.platform import Type as PlatformType

from slither.core.declarations import Contract
from slither.tools.properties.addresses.address import Addresses
from slither.tools.properties.platforms.echidna import generate_echidna_config
from slither.tools.properties.properties.ercs.erc20.properties.burn import ERC20_NotBurnable
from slither.tools.properties.properties.ercs.erc20.properties.initialization import ERC20_CONFIG
from slither.tools.properties.properties.ercs.erc20.properties.mint import ERC20_NotMintable
from slither.tools.properties.properties.ercs.erc20.properties.mint_and_burn import (
    ERC20_NotMintableNotBurnable,
)
from slither.tools.properties.properties.ercs.erc20.properties.transfer import (
    ERC20_Transferable,
    ERC20_Pausable,
)
from slither.tools.properties.properties.ercs.erc20.unit_tests.truffle import generate_truffle_test
from slither.tools.properties.properties.properties import (
    property_to_solidity,
    Property,
)
from slither.tools.properties.solidity.generate_properties import (
    generate_solidity_properties,
    generate_test_contract,
    generate_solidity_interface,
)
from slither.utils.colors import red, green

logger = logging.getLogger("Slither")

PropertyDescription = namedtuple("PropertyDescription", ["properties", "description"])

ERC20_PROPERTIES = {
    "Transferable": PropertyDescription(ERC20_Transferable, "Test the correct tokens transfer"),
    "Pausable": PropertyDescription(ERC20_Pausable, "Test the pausable functionality"),
    "NotMintable": PropertyDescription(ERC20_NotMintable, "Test that no one can mint tokens"),
    "NotMintableNotBurnable": PropertyDescription(
        ERC20_NotMintableNotBurnable, "Test that no one can mint or burn tokens"
    ),
    "NotBurnable": PropertyDescription(ERC20_NotBurnable, "Test that no one can burn tokens"),
    "Burnable": PropertyDescription(
        ERC20_NotBurnable,
        'Test the burn of tokens. Require the "burn(address) returns()" function',
    ),
}


def generate_erc20(
    contract: Contract, type_property: str, addresses: Addresses
):  # pylint: disable=too-many-locals
    """
    Generate the ERC20 tests
    Files generated:
    - interfaces.sol: generic crytic interface
    - Properties[CONTRACTNAME].sol: erc20 properties
    - Test[CONTRACTNAME].sol: Target, its constructor needs to be manually updated
    - If truffle
        - migrations/x_Test[CONTRACTNAME].js
        - test/crytic/InitializationTest[CONTRACTNAME].js: unit tests to check that the contract is correctly configured
        - test/crytic/Test[CONTRACTNAME].js: ERC20 checks
    - echidna_config.yaml: configuration file
    :param addresses:
    :param contract:
    :param type_property: One of ERC20_PROPERTIES.keys()
    :return:
    """
    if contract.compilation_unit.core.crytic_compile is None:
        logging.error("Please compile with crytic-compile")
        return
    if contract.compilation_unit.core.crytic_compile.type not in [
        PlatformType.TRUFFLE,
        PlatformType.SOLC,
    ]:
        logging.error(
            f"{contract.compilation_unit.core.crytic_compile.type} not yet supported by slither-prop"
        )
        return

    # Check if the contract is an ERC20 contract and if the functions have the correct visibility
    errors = _check_compatibility(contract)
    if errors:
        logger.error(red(errors))
        return

    erc_properties = ERC20_PROPERTIES.get(type_property, None)
    if erc_properties is None:
        logger.error(f"{type_property} unknown. Types available {ERC20_PROPERTIES.keys()}")
        return
    properties = erc_properties.properties

    # Generate the output directory
    output_dir = _platform_to_output_dir(contract.compilation_unit.core.crytic_compile.platform)
    output_dir.mkdir(exist_ok=True)

    # Get the properties
    solidity_properties, unit_tests = _get_properties(contract, properties)

    # Generate the contract containing the properties
    generate_solidity_interface(output_dir, addresses)
    property_file = generate_solidity_properties(
        contract, type_property, solidity_properties, output_dir
    )

    # Generate the Test contract
    initialization_recommendation = _initialization_recommendation(type_property)
    contract_filename, contract_name = generate_test_contract(
        contract,
        type_property,
        output_dir,
        property_file,
        initialization_recommendation,
    )

    # Generate Echidna config file
    echidna_config_filename = generate_echidna_config(
        Path(contract.compilation_unit.core.crytic_compile.target).parent, addresses
    )

    unit_test_info = ""

    # If truffle, generate unit tests
    if contract.compilation_unit.core.crytic_compile.type == PlatformType.TRUFFLE:
        unit_test_info = generate_truffle_test(contract, type_property, unit_tests, addresses)

    logger.info("################################################")
    logger.info(green(f"Update the constructor in {Path(output_dir, contract_filename)}"))

    if unit_test_info:
        logger.info(green(unit_test_info))

    logger.info(green("To run Echidna:"))
    txt = f"\t echidna-test {contract.compilation_unit.core.crytic_compile.target} "
    txt += f"--contract {contract_name} --config {echidna_config_filename}"
    logger.info(green(txt))


def _initialization_recommendation(type_property: str) -> str:
    content = ""
    content += "\t\t// Add below a minimal configuration:\n"
    content += "\t\t// - crytic_owner must have some tokens \n"
    content += "\t\t// - crytic_user must have some tokens \n"
    content += "\t\t// - crytic_attacker must have some tokens \n"
    if type_property in ["Pausable"]:
        content += "\t\t// - The contract must be paused \n"
    if type_property in ["NotMintable", "NotMintableNotBurnable"]:
        content += "\t\t// - The contract must not be mintable \n"
    if type_property in ["NotBurnable", "NotMintableNotBurnable"]:
        content += "\t\t// - The contract must not be burnable \n"
    content += "\n"
    content += "\n"

    return content


# TODO: move this to crytic-compile
def _platform_to_output_dir(platform: AbstractPlatform) -> Path:
    if platform.TYPE == PlatformType.TRUFFLE:
        return Path(platform.target, "contracts", "crytic")
    if platform.TYPE == PlatformType.SOLC:
        return Path(platform.target).parent
    return Path()


def _check_compatibility(contract):
    errors = ""
    if not contract.is_erc20():
        errors = f"{contract} is not ERC20 compliant. Consider checking the contract with slither-check-erc"
        return errors

    transfer = contract.get_function_from_signature("transfer(address,uint256)")

    if transfer.visibility != "public":
        errors = f"slither-prop requires {transfer.canonical_name} to be public. Please change the visibility"

    transfer_from = contract.get_function_from_signature("transferFrom(address,address,uint256)")
    if transfer_from.visibility != "public":
        if errors:
            errors += "\n"
        errors += f"slither-prop requires {transfer_from.canonical_name} to be public. Please change the visibility"

    approve = contract.get_function_from_signature("approve(address,uint256)")
    if approve.visibility != "public":
        if errors:
            errors += "\n"
        errors += f"slither-prop requires {approve.canonical_name} to be public. Please change the visibility"

    return errors


def _get_properties(contract, properties: List[Property]) -> Tuple[str, List[Property]]:
    solidity_properties = ""

    if contract.compilation_unit.crytic_compile.type == PlatformType.TRUFFLE:
        solidity_properties += "\n".join([property_to_solidity(p) for p in ERC20_CONFIG])

    solidity_properties += "\n".join([property_to_solidity(p) for p in properties])
    unit_tests = [p for p in properties if p.is_unit_test]

    return solidity_properties, unit_tests
