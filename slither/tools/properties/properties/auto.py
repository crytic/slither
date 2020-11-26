import logging
import json
import hashlib

from collections import namedtuple
from pathlib import Path
from typing import Tuple, List

from crytic_compile.platform.abstract_platform import AbstractPlatform
from crytic_compile.platform import Type as PlatformType

from slither.core.declarations import Contract
from slither.utils.function import get_function_id
from slither.tools.properties.addresses.address import Addresses

from slither.tools.properties.platforms.echidna import generate_echidna_auto_config
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
    PropertyType,
    PropertyReturn,
    PropertyCaller,
)
from slither.tools.properties.solidity.generate_properties import (
    generate_solidity_properties_no_contract,
    generate_test_contract_no_contract,
    generate_solidity_interface,
)

from slither.utils.colors import red, green

logger = logging.getLogger("Slither")

PropertyDescription = namedtuple("PropertyDescription", ["properties", "description"])

def checksum_encode(hex_addr): # Takes a 20-byte binary address as input
    #hex_addr = addr.hex()
    hex_addr = hex_addr.lower().replace("0x","")
    checksummed_buffer = ""

    # Treat the hex address as ascii/utf-8 for keccak256 hashing
    hashed_address = hashlib.sha3_512(hex_addr.encode("utf-8")).hexdigest()
    #print(hex_addr.encode("utf-8"), hashlib.sha3_512(hex_addr.encode("utf-8")), hashed_address)

    # Iterate over each character in the hex address
    for nibble_index, character in enumerate(hex_addr):

        if character in "0123456789":
            # We can't upper-case the decimal digits
            checksummed_buffer += character
        elif character in "abcdef":
            # Check if the corresponding hex digit (nibble) in the hash is 8 or higher
            hashed_address_nibble = int(hashed_address[nibble_index], 16)
            if hashed_address_nibble > 7:
                checksummed_buffer += character.upper()
            else:
                checksummed_buffer += character
        else:
            print(f"Unrecognized hex character {character!r} at position {nibble_index}")
            assert(False)
            #raise eth_utils.ValidationError(
            #    f"Unrecognized hex character {character!r} at position {nibble_index}"
            #)

    return "0x" + checksummed_buffer

def AUTO_token_max(attacker_address, tokens): 
    ps = []
    for token,max_balance in tokens.items():
        ps.append(Property(
            name="crytic_attacker_cannot_get_tokens_from_" + token.replace("0x","") + "()",
            description="The attacker address should not receive tokens.",
            content="\n\t\treturn HasBalance(address("+ str(int(token,16)) +")).balanceOf(address(" + attacker_address + ")) <= " + str(max_balance) + " ;",
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
    sel = hex(sel).replace("0x","")
    sel = "0"*(8-len(sel)) + sel 

    t = t.lower().replace("0x", "")
    t = "0"*(64-len(t)) + t

    v = hex(v).replace("0x","")
    v = "0"*(64-len(v)) + v

    data = "0x" + sel + t + v
    return ({"event": "FunctionCall", "from": f, "to": c, "gas_used": "0x1", "gas_price": "0x1", "data": data, "value": "0x0"})


def detect_token_props(slither, txs, attacker_address, max_balance):

    accounts = set()
    contracts = dict()
    last_create = None

    if max_balance is None:
        max_balance = 0

    # obtain the list of contracts and accounts used
    for i,tx in enumerate(txs):
        if tx["event"] == "ContractCreated":
            accounts.add(tx["from"])
            contracts[tx["contract_address"]] = None
            last_create = i

        elif tx["event"] == "FunctionCall":
            if tx["to"] not in contracts:
                contracts[tx["to"]] = None

            accounts.add(tx["from"])
            selector = tx["data"][:10]
            found = False
            #print(selector)
            for contract in slither.contracts_derived:
                #if str(contract) == "BFactory":
                #    for signature in contract.functions_signatures:
                #        print(signature, hex(get_function_id(signature)))
                #    #assert(False)

                for signature in contract.functions_signatures:
                    fid = get_function_id(signature)
                    if int(selector,16) == fid:
                        found = True
                        #print(contracts[tx["to"]], contract)
                        assert(tx["to"] in contracts)
                        if (contracts[tx["to"]] is not None and contracts[tx["to"]] != contract):
                            if set( contracts[tx["to"]].functions_signatures ).issubset( contract.functions_signatures ):
                                #print("upgrading", contracts[tx["to"]], "to", contract)
                                contracts[tx["to"]] = contract
                            else:
                                pass     
                                #print("not upgrading", contracts[tx["to"]], "to", contract)

                            #assert(False)
                        else:
                            contracts[tx["to"]] = contract
                        #print(tx, "was parsed as", signature, "from contract", contract) 
                        break
             
            if not found:
                print(tx, "from contract", contracts[tx["to"]], "not parsed")
                #assert(False) 

    #print("accounts", accounts)
    print("Echidna should generate transactions from accounts", list(accounts), "as well as the ones controlled by an attacker")
    print("List of detected properties:")
    tokens = dict()
    itxs = []

    for (addr,contract) in contracts.items():
        if contract is None:
            continue
        if 'balanceOf(address)' in contract.functions_signatures:
            print("Found one token-like contract at", addr, "(", str(contract) ,")")
            tokens[addr] = max_balance
            """
            sig = 'transfer(address,uint256)'            
            if sig in contract.functions_signatures and max_balance > 0:

                for account in accounts:
                    itxs.append(encode_transfer(sig, account, attacker_address, addr, max_balance))

                tokens[addr] = max_tokens
                print("Attacker should have no more than", max_tokens, "tokens in", addr)

            sig = 'approve(address,uint256)'
            if sig in contract.functions_signatures and max_balance > 0:
                for (spender, _) in contracts.items():
                    itxs.append(encode_transfer(sig, attacker_address, spender, addr, 2**255))
                print("The attacker allows any contract to take its tokens")
            """

    return (accounts, tokens, txs[:last_create+1]+itxs, txs[last_create+1:])

def generate_auto(
    slither, filename, addresses, max_balance, crytic_args
    #contract: Contract, type_propertyi: str, addresses: Addresses
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
    txs = json.load(open(filename))
    (accounts, tokens, init_txs, samples_txs) = detect_token_props(slither, txs, addresses.attacker, max_balance)
    
    properties = AUTO_token_max(addresses.attacker, tokens)
    #print(properties)
 
    # Generate the output directory
    output_dir = _platform_to_output_dir(slither.crytic_compile.platform)
    output_dir.mkdir(exist_ok=True)

    # Get the properties
    solidity_properties, unit_tests = _get_properties(slither, properties)

    #print(solidity_properties)

    # Generate the contract containing the properties
    generate_solidity_interface(output_dir, addresses)
    type_property = "AUTO"

    property_file = generate_solidity_properties_no_contract(
        type_property, solidity_properties, output_dir
    )

    # Generate the Test contract
    #initialization_recommendation = _initialization_recommendation(type_property)
    contract_filename, contract_name = generate_test_contract_no_contract(
        type_property, output_dir, property_file
    )

    print("Saving JSON with init transactions")
    init_file = filename + ".init"
    with open(init_file, 'w') as outfile:
        json.dump(init_txs, outfile)

    print("Saving JSON with sample transactions")
    samples_file = filename + ".samples"
    with open(samples_file, 'w') as outfile:
        json.dump(samples_txs, outfile)

    # Add attacker address to the list of accounts
    accounts.add(addresses.attacker)
    # Generate Echidna config file
    echidna_config_filename = generate_echidna_auto_config(".", list(accounts), init_file, samples_file, crytic_args)

    #unit_test_info = ""

    # If truffle, generate unit tests
    #if contract.slither.crytic_compile.type == PlatformType.TRUFFLE:
    #    unit_test_info = generate_truffle_test(contract, type_property, unit_tests, addresses)

    #logger.info("################################################")
    #logger.info(green(f"Update the constructor in {Path(output_dir, contract_filename)}"))

    #if unit_test_info:
    #    logger.info(green(unit_test_info))

    logger.info(green("To run Echidna:"))
    txt = f"\t echidna-test {slither.crytic_compile.target} "
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
    elif platform.TYPE == PlatformType.BUILDER:
        return Path(platform.target, "contracts", "crytic")
    elif platform.TYPE == PlatformType.SOLC:
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


def _get_properties(slither, properties: List[Property]) -> Tuple[str, List[Property]]:
    solidity_properties = ""

    #if slither.crytic_compile.type == PlatformType.TRUFFLE:
    #    solidity_properties += "\n".join([property_to_solidity(p) for p in ERC20_CONFIG])

    solidity_properties += "\n".join([property_to_solidity(p) for p in properties])
    unit_tests = [p for p in properties if p.is_unit_test]

    return solidity_properties, unit_tests
