import logging
from pathlib import Path
from typing import Tuple

from slither.core.declarations import Contract
from slither.tools.properties.addresses.address import Addresses
from slither.tools.properties.utils import write_file

logger = logging.getLogger("Slither")


def generate_solidity_properties(
    contract: Contract, type_property: str, solidity_properties: str, output_dir: Path
) -> Path:

    solidity_import = 'import "./interfaces.sol";\n'
    solidity_import += f'import "../{contract.source_mapping["filename_short"]}";'

    test_contract_name = f"Properties{contract.name}{type_property}"

    solidity_content = (
        f"{solidity_import}\ncontract {test_contract_name} is CryticInterface,{contract.name}"
    )
    solidity_content += f"{{\n\n{solidity_properties}\n}}\n"

    filename = f"{test_contract_name}.sol"
    write_file(output_dir, filename, solidity_content)

    return Path(filename)


def generate_test_contract(
    contract: Contract,
    type_property: str,
    output_dir: Path,
    property_file: Path,
    initialization_recommendation: str,
) -> Tuple[str, str]:
    test_contract_name = f"Test{contract.name}{type_property}"
    properties_name = f"Properties{contract.name}{type_property}"

    content = ""
    content += f'import "./{property_file}";\n'
    content += f"contract {test_contract_name} is {properties_name} {{\n"
    content += "\tconstructor() public{\n"
    content += "\t\t// Existing addresses:\n"
    content += "\t\t// - crytic_owner: If the contract has an owner, it must be crytic_owner\n"
    content += "\t\t// - crytic_user: Legitimate user\n"
    content += "\t\t// - crytic_attacker: Attacker\n"
    content += "\t\t// \n"
    content += initialization_recommendation
    content += "\t\t// \n"
    content += "\t\t// \n"
    content += "\t\t// Update the following if totalSupply and balanceOf are external functions or state variables:\n\n"
    content += "\t\tinitialTotalSupply = totalSupply();\n"
    content += "\t\tinitialBalance_owner = balanceOf(crytic_owner);\n"
    content += "\t\tinitialBalance_user = balanceOf(crytic_user);\n"
    content += "\t\tinitialBalance_attacker = balanceOf(crytic_attacker);\n"

    content += "\t}\n}\n"

    filename = f"{test_contract_name}.sol"
    write_file(output_dir, filename, content, allow_overwrite=False)

    return filename, test_contract_name


def generate_solidity_interface(output_dir: Path, addresses: Addresses):
    content = f"""
contract CryticInterface{{
    address internal crytic_owner = address({addresses.owner});
    address internal crytic_user = address({addresses.user});
    address internal crytic_attacker = address({addresses.attacker});
    uint internal initialTotalSupply;
    uint internal initialBalance_owner;
    uint internal initialBalance_user;
    uint internal initialBalance_attacker;
}}"""

    # Static file, we discard if it exists as it should never change
    write_file(output_dir, "interfaces.sol", content, discard_if_exist=True)
