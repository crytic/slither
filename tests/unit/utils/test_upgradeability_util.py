import os
from pathlib import Path

from slither import Slither
from slither.core.expressions import Literal
from slither.utils.upgradeability import (
    compare,
    get_proxy_implementation_var,
    get_proxy_implementation_slot,
)

SLITHER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" / "upgradeability_util"


# pylint: disable=too-many-locals
def test_upgrades_compare(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.2")

    sl = Slither(os.path.join(TEST_DATA_DIR, "TestUpgrades-0.8.2.sol"), solc=solc_path)
    v1 = sl.get_contract_from_name("ContractV1")[0]
    v2 = sl.get_contract_from_name("ContractV2")[0]
    (
        missing_vars,
        new_vars,
        tainted_vars,
        new_funcs,
        modified_funcs,
        tainted_funcs,
        tainted_contracts,
    ) = compare(v1, v2, include_external=True)
    assert len(missing_vars) == 0
    assert new_vars == [v2.get_state_variable_from_name("stateC")]
    assert tainted_vars == [
        v2.get_state_variable_from_name("bug"),
    ]
    assert new_funcs == [
        v2.get_function_from_signature("i()"),
        v2.get_function_from_signature("erc20Transfer(address,address,uint256)"),
    ]
    assert modified_funcs == [v2.get_function_from_signature("checkB()")]
    assert tainted_funcs == [
        v2.get_function_from_signature("h()"),
    ]
    erc20 = sl.get_contract_from_name("ERC20")[0]
    assert len(tainted_contracts) == 1
    assert tainted_contracts[0].contract == erc20
    assert set(tainted_contracts[0].tainted_functions) == {
        erc20.get_function_from_signature("transfer(address,uint256)"),
        erc20.get_function_from_signature("_transfer(address,address,uint256)"),
        erc20.get_function_from_signature("_burn(address,uint256)"),
        erc20.get_function_from_signature("balanceOf(address)"),
        erc20.get_function_from_signature("_mint(address,uint256)"),
    }
    assert tainted_contracts[0].tainted_variables == [
        erc20.get_state_variable_from_name("_balances")
    ]


def test_upgrades_implementation_var(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.2")
    sl = Slither(os.path.join(TEST_DATA_DIR, "TestUpgrades-0.8.2.sol"), solc=solc_path)

    erc_1967_proxy = sl.get_contract_from_name("ERC1967Proxy")[0]
    storage_proxy = sl.get_contract_from_name("InheritedStorageProxy")[0]

    target = get_proxy_implementation_var(erc_1967_proxy)
    slot = get_proxy_implementation_slot(erc_1967_proxy)
    assert target == erc_1967_proxy.get_state_variable_from_name("_IMPLEMENTATION_SLOT")
    assert slot.slot == 0x360894A13BA1A3210667C828492DB98DCA3E2076CC3735A920A3CA505D382BBC
    target = get_proxy_implementation_var(storage_proxy)
    slot = get_proxy_implementation_slot(storage_proxy)
    assert target == storage_proxy.get_state_variable_from_name("implementation")
    assert slot.slot == 1

    solc_path = solc_binary_path("0.5.0")
    sl = Slither(os.path.join(TEST_DATA_DIR, "TestUpgrades-0.5.0.sol"), solc=solc_path)

    eip_1822_proxy = sl.get_contract_from_name("EIP1822Proxy")[0]
    # zos_proxy = sl.get_contract_from_name("ZosProxy")[0]
    master_copy_proxy = sl.get_contract_from_name("MasterCopyProxy")[0]
    synth_proxy = sl.get_contract_from_name("SynthProxy")[0]

    target = get_proxy_implementation_var(eip_1822_proxy)
    slot = get_proxy_implementation_slot(eip_1822_proxy)
    assert target not in eip_1822_proxy.state_variables_ordered
    assert target.name == "contractLogic" and isinstance(target.expression, Literal)
    assert (
        target.expression.value
        == "0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7"
    )
    assert slot.slot == 0xC5F16F0FCC639FA48A6947836D9850F504798523BF8C9A3A87D5876CF622BCF7
    # # The util fails with this proxy due to how Slither parses assembly w/ Solidity versions < 0.6.0 (see issue #1775)
    # target = get_proxy_implementation_var(zos_proxy)
    # slot = get_proxy_implementation_slot(zos_proxy)
    # assert target == zos_proxy.get_state_variable_from_name("IMPLEMENTATION_SLOT")
    # assert slot.slot == 0x7050C9E0F4CA769C69BD3A8EF740BC37934F8E2C036E5A723FD8EE048ED3F8C3
    target = get_proxy_implementation_var(master_copy_proxy)
    slot = get_proxy_implementation_slot(master_copy_proxy)
    assert target == master_copy_proxy.get_state_variable_from_name("masterCopy")
    assert slot.slot == 0
    target = get_proxy_implementation_var(synth_proxy)
    slot = get_proxy_implementation_slot(synth_proxy)
    assert target == synth_proxy.get_state_variable_from_name("target")
    assert slot.slot == 1
