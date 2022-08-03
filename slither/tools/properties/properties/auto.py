import json
import logging
from collections import namedtuple, OrderedDict
from pathlib import Path
from typing import Tuple, List

from crytic_compile.platform import Type as PlatformType
from crytic_compile.platform.abstract_platform import AbstractPlatform

from slither.tools.properties.platforms.echidna import generate_echidna_auto_config
from slither.tools.properties.properties.properties import (
    property_to_solidity,
    Property,
    PropertyType,
    PropertyReturn,
    PropertyCaller,
)
from slither.tools.properties.solidity.generate_properties import (
    generate_solidity_properties_no_contract,
    generate_test_contract_no_contract,
    generate_solidity_interface,
)
from slither.utils.colors import green
from slither.utils.function import get_function_id

logger = logging.getLogger("Slither")

PropertyDescription = namedtuple("PropertyDescription", ["properties", "description"])


def AUTO_token_max(attacker_address, tokens):
    ps = []
    for token, max_balance in tokens.items():
        ps.append(
            Property(
                name="crytic_attacker_cannot_get_tokens_more_than_"
                + str(max_balance)
                + "_from_"
                + token.replace("0x", "")
                + "()",
                description="The attacker address should not receive tokens.",
                content="\n\t\treturn HasBalance(address("
                + str(int(token, 16))
                + ")).balanceOf(address("
                + str(int(attacker_address, 16))
                + ")) <= "
                + str(max_balance)
                + " ;",
                type=PropertyType.CODE_QUALITY,
                return_type=PropertyReturn.SUCCESS,
                is_unit_test=False,
                is_property_test=True,
                caller=PropertyCaller.ANY,
            )
        )
    return ps


def encode_transfer(sig, f, t, c, v):

    sel = get_function_id(sig)
    sel = hex(sel).replace("0x", "")
    sel = "0" * (8 - len(sel)) + sel

    t = t.lower().replace("0x", "")
    t = "0" * (64 - len(t)) + t

    v = hex(v).replace("0x", "")
    v = "0" * (64 - len(v)) + v

    data = "0x" + sel + t + v
    return {
        "event": "FunctionCall",
        "from": f,
        "to": c,
        "gas_used": "0x1",
        "gas_price": "0x1",
        "data": data,
        "value": "0x0",
    }


# TODO: refactor to remove the lint exception
# pylint: disable=too-many-locals,too-many-branches
def detect_token_props(slither, txs, max_balance):

    accounts = set()
    contracts = {}
    tokens = OrderedDict()
    erc20_sigs = [
        get_function_id("transfer(address,uint256)"),
        get_function_id("balanceOf(address)"),
        get_function_id("approve(address,uint256)"),
    ]

    if max_balance is None:
        max_balance = 0

    for contract in slither.contracts:
        bc = slither.crytic_compile.bytecode_init(contract.name)
        contracts[bc] = contract

    # obtain the list of contracts and accounts used
    print("List of transactions:")
    for tx in txs:
        if tx["event"] == "ContractCreated":
            bytecode = tx["data"].replace("0x", "")
            if bytecode in contracts:
                print("DEPLOYED", contracts[bytecode], "at", tx["contract_address"])
            else:
                print("CREATE", "at", tx["contract_address"])
            accounts.add(tx["from"])

        elif tx["event"] == "FunctionCall":

            addr = tx["to"]
            accounts.add(tx["from"])
            selector = tx["data"][:10]
            found = False
            for contract in slither.contracts_derived:
                if found:
                    break
                for signature in contract.functions_signatures:
                    if found:
                        break
                    fid = get_function_id(signature)
                    if int(selector, 16) == fid:
                        print(tx["from"], "called", signature, "in", addr)
                        found = True

            if int(selector, 16) in erc20_sigs:
                tokens[addr] = max_balance

    print("Found the following accounts:", ", ".join(accounts))
    for (addr, _) in tokens.items():
        print("Found one token-like contract at", addr)

    return (accounts, tokens)


def generate_auto(
    slither, filename, addresses, max_balance, crytic_args
):  # pylint: disable=too-many-locals
    """
    Generate the AUTO tests
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
    with open(filename, encoding="utf8") as file_desc:
        txs = json.load(file_desc)
    # (accounts, tokens, init_txs, samples_txs ) = detect_token_props(slither, txs, addresses.attacker, max_balance)
    (_, tokens) = detect_token_props(slither, txs, max_balance)

    properties = AUTO_token_max(addresses.attacker, tokens)
    # print(properties)

    # Generate the output directory
    output_dir = _platform_to_output_dir(slither.crytic_compile.platform)
    output_dir.mkdir(exist_ok=True)

    # Get the properties
    solidity_properties, _ = _get_properties(properties)

    # print(solidity_properties)

    # Generate the contract containing the properties
    generate_solidity_interface(output_dir, addresses)
    type_property = "AUTO"

    property_file = generate_solidity_properties_no_contract(
        type_property, solidity_properties, output_dir
    )

    # Generate the Test contract
    _, contract_name = generate_test_contract_no_contract(type_property, output_dir, property_file)

    # Add attacker address to the list of accounts
    # accounts.add(addresses.attacker)
    # Generate Echidna config file
    echidna_config_filename = generate_echidna_auto_config(
        ".", [addresses.attacker], filename, crytic_args
    )

    logger.info(green("To run Echidna:"))
    txt = f"\t echidna-test {slither.crytic_compile.target} "
    txt += f"--contract {contract_name} --config {echidna_config_filename}"
    logger.info(green(txt))


# TODO: move this to crytic-compile
def _platform_to_output_dir(platform: AbstractPlatform) -> Path:
    if platform.TYPE == PlatformType.TRUFFLE:
        return Path(platform.target, "contracts", "crytic")
    if platform.TYPE == PlatformType.BUILDER:
        return Path(platform.target, "contracts", "crytic")
    if platform.TYPE == PlatformType.SOLC:
        return Path(platform.target).parent
    return Path()


def _get_properties(properties: List[Property]) -> Tuple[str, List[Property]]:
    solidity_properties = ""

    # if slither.crytic_compile.type == PlatformType.TRUFFLE:
    #    solidity_properties += "\n".join([property_to_solidity(p) for p in ERC20_CONFIG])

    solidity_properties += "\n".join([property_to_solidity(p) for p in properties])
    unit_tests = [p for p in properties if p.is_unit_test]

    return solidity_properties, unit_tests
