from pathlib import Path
from typing import Optional, TYPE_CHECKING
from hashlib import sha1
from slither.utils.oz_hashes import oz_hashes

if TYPE_CHECKING:
    from slither.core.declarations import Contract

libraries = {
    "Openzeppelin-SafeMath": lambda x: is_openzeppelin_safemath(x),
    "Openzeppelin-ECRecovery": lambda x: is_openzeppelin_ecrecovery(x),
    "Openzeppelin-Ownable": lambda x: is_openzeppelin_ownable(x),
    "Openzeppelin-ERC20": lambda x: is_openzeppelin_erc20(x),
    "Openzeppelin-ERC721": lambda x: is_openzeppelin_erc721(x),
    "Zos-Upgrade": lambda x: is_zos_initializable(x),
    "Dapphub-DSAuth": lambda x: is_dapphub_ds_auth(x),
    "Dapphub-DSMath": lambda x: is_dapphub_ds_math(x),
    "Dapphub-DSToken": lambda x: is_dapphub_ds_token(x),
    "Dapphub-DSProxy": lambda x: is_dapphub_ds_proxy(x),
    "Dapphub-DSGroup": lambda x: is_dapphub_ds_group(x),
    "AragonOS-SafeMath": lambda x: is_aragonos_safemath(x),
    "AragonOS-ERC20": lambda x: is_aragonos_erc20(x),
    "AragonOS-AppProxyBase": lambda x: is_aragonos_app_proxy_base(x),
    "AragonOS-AppProxyPinned": lambda x: is_aragonos_app_proxy_pinned(x),
    "AragonOS-AppProxyUpgradeable": lambda x: is_aragonos_app_proxy_upgradeable(x),
    "AragonOS-AppStorage": lambda x: is_aragonos_app_storage(x),
    "AragonOS-AragonApp": lambda x: is_aragonos_aragon_app(x),
    "AragonOS-UnsafeAragonApp": lambda x: is_aragonos_unsafe_aragon_app(x),
    "AragonOS-Autopetrified": lambda x: is_aragonos_autopetrified(x),
    "AragonOS-DelegateProxy": lambda x: is_aragonos_delegate_proxy(x),
    "AragonOS-DepositableDelegateProxy": lambda x: is_aragonos_depositable_delegate_proxy(x),
    "AragonOS-DepositableStorage": lambda x: is_aragonos_delegate_proxy(x),
    "AragonOS-Initializable": lambda x: is_aragonos_initializable(x),
    "AragonOS-IsContract": lambda x: is_aragonos_is_contract(x),
    "AragonOS-Petrifiable": lambda x: is_aragonos_petrifiable(x),
    "AragonOS-ReentrancyGuard": lambda x: is_aragonos_reentrancy_guard(x),
    "AragonOS-TimeHelpers": lambda x: is_aragonos_time_helpers(x),
    "AragonOS-VaultRecoverable": lambda x: is_aragonos_vault_recoverable(x),
}


def is_standard_library(contract: "Contract") -> Optional[str]:
    for name, is_lib in libraries.items():
        if is_lib(contract):
            return name
    return None


###################################################################################
###################################################################################
# region General libraries
###################################################################################
###################################################################################


def is_openzeppelin(contract: "Contract") -> bool:
    if not contract.is_from_dependency():
        return False
    path = Path(contract.source_mapping.filename.absolute).parts
    is_zep = "openzeppelin-solidity" in Path(contract.source_mapping.filename.absolute).parts
    try:
        is_zep |= path[path.index("@openzeppelin") + 1] == "contracts"
    except IndexError:
        pass
    except ValueError:
        pass
    return is_zep


def is_openzeppelin_strict(contract: "Contract") -> bool:
    source_hash = sha1(contract.source_mapping.content.encode("utf-8")).hexdigest()
    return source_hash in oz_hashes


def is_zos(contract: "Contract") -> bool:
    if not contract.is_from_dependency():
        return False
    return "zos-lib" in Path(contract.source_mapping.filename.absolute).parts


def is_aragonos(contract: "Contract") -> bool:
    if not contract.is_from_dependency():
        return False
    return "@aragon/os" in Path(contract.source_mapping.filename.absolute).parts


# endregion
###################################################################################
###################################################################################
# region SafeMath
###################################################################################
###################################################################################


def is_safemath(contract: "Contract") -> bool:
    return contract.name == "SafeMath"


def is_openzeppelin_safemath(contract: "Contract") -> bool:
    return is_safemath(contract) and is_openzeppelin(contract)


def is_aragonos_safemath(contract: "Contract") -> bool:
    return is_safemath(contract) and is_aragonos(contract)


# endregion
###################################################################################
###################################################################################
# region ECRecovery
###################################################################################
###################################################################################


def is_ecrecovery(contract: "Contract") -> bool:
    return contract.name == "ECRecovery"


def is_openzeppelin_ecrecovery(contract: "Contract") -> bool:
    return is_ecrecovery(contract) and is_openzeppelin(contract)


# endregion
###################################################################################
###################################################################################
# region Ownable
###################################################################################
###################################################################################


def is_ownable(contract: "Contract") -> bool:
    return contract.name == "Ownable"


def is_openzeppelin_ownable(contract: "Contract") -> bool:
    return is_ownable(contract) and is_openzeppelin(contract)


# endregion
###################################################################################
###################################################################################
# region ERC20
###################################################################################
###################################################################################


def is_erc20(contract: "Contract") -> bool:
    return contract.name == "ERC20"


def is_openzeppelin_erc20(contract: "Contract") -> bool:
    return is_erc20(contract) and is_openzeppelin(contract)


def is_aragonos_erc20(contract: "Contract") -> bool:
    return is_erc20(contract) and is_aragonos(contract)


# endregion
###################################################################################
###################################################################################
# region ERC721
###################################################################################
###################################################################################


def is_erc721(contract: "Contract") -> bool:
    return contract.name == "ERC721"


def is_openzeppelin_erc721(contract: "Contract") -> bool:
    return is_erc721(contract) and is_openzeppelin(contract)


# endregion
###################################################################################
###################################################################################
# region Zos Initializable
###################################################################################
###################################################################################


def is_initializable(contract: "Contract") -> bool:
    return contract.name == "Initializable"


def is_zos_initializable(contract: "Contract") -> bool:
    return is_initializable(contract) and is_zos(contract)


# endregion
###################################################################################
###################################################################################
# region DappHub
###################################################################################
###################################################################################

dapphubs = {
    "DSAuth": "ds-auth",
    "DSMath": "ds-math",
    "DSToken": "ds-token",
    "DSProxy": "ds-proxy",
    "DSGroup": "ds-group",
}


def _is_ds(contract: "Contract", name: str) -> bool:
    return contract.name == name


def _is_dappdhub_ds(contract: "Contract", name: str) -> bool:
    if not contract.is_from_dependency():
        return False
    if not dapphubs[name] in Path(contract.source_mapping.filename.absolute).parts:
        return False
    return _is_ds(contract, name)


def is_ds_auth(contract: "Contract") -> bool:
    return _is_ds(contract, "DSAuth")


def is_dapphub_ds_auth(contract: "Contract") -> bool:
    return _is_dappdhub_ds(contract, "DSAuth")


def is_ds_math(contract: "Contract") -> bool:
    return _is_ds(contract, "DSMath")


def is_dapphub_ds_math(contract: "Contract") -> bool:
    return _is_dappdhub_ds(contract, "DSMath")


def is_ds_token(contract: "Contract") -> bool:
    return _is_ds(contract, "DSToken")


def is_dapphub_ds_token(contract: "Contract") -> bool:
    return _is_dappdhub_ds(contract, "DSToken")


def is_ds_proxy(contract: "Contract") -> bool:
    return _is_ds(contract, "DSProxy")


def is_dapphub_ds_proxy(contract: "Contract") -> bool:
    return _is_dappdhub_ds(contract, "DSProxy")


def is_ds_group(contract: "Contract") -> bool:
    return _is_ds(contract, "DSGroup")


def is_dapphub_ds_group(contract: "Contract") -> bool:
    return _is_dappdhub_ds(contract, "DSGroup")


# endregion
###################################################################################
###################################################################################
# region Aragon
###################################################################################
###################################################################################


def is_aragonos_app_proxy_base(contract: "Contract") -> bool:
    return contract.name == "AppProxyBase" and is_aragonos(contract)


def is_aragonos_app_proxy_pinned(contract: "Contract") -> bool:
    return contract.name == "AppProxyPinned" and is_aragonos(contract)


def is_aragonos_app_proxy_upgradeable(contract: "Contract") -> bool:
    return contract.name == "AppProxyUpgradeable" and is_aragonos(contract)


def is_aragonos_app_storage(contract: "Contract") -> bool:
    return contract.name == "AppStorage" and is_aragonos(contract)


def is_aragonos_aragon_app(contract: "Contract") -> bool:
    return contract.name == "AragonApp" and is_aragonos(contract)


def is_aragonos_unsafe_aragon_app(contract: "Contract") -> bool:
    return contract.name == "UnsafeAragonApp" and is_aragonos(contract)


def is_aragonos_autopetrified(contract: "Contract") -> bool:
    return contract.name == "Autopetrified" and is_aragonos(contract)


def is_aragonos_delegate_proxy(contract: "Contract") -> bool:
    return contract.name == "DelegateProxy" and is_aragonos(contract)


def is_aragonos_depositable_delegate_proxy(contract: "Contract") -> bool:
    return contract.name == "DepositableDelegateProxy" and is_aragonos(contract)


def is_aragonos_depositable_storage(contract: "Contract") -> bool:
    return contract.name == "DepositableStorage" and is_aragonos(contract)


def is_aragonos_ether_token_contract(contract: "Contract") -> bool:
    return contract.name == "EtherTokenConstant" and is_aragonos(contract)


def is_aragonos_initializable(contract: "Contract") -> bool:
    return contract.name == "Initializable" and is_aragonos(contract)


def is_aragonos_is_contract(contract: "Contract") -> bool:
    return contract.name == "IsContract" and is_aragonos(contract)


def is_aragonos_petrifiable(contract: "Contract") -> bool:
    return contract.name == "Petrifiable" and is_aragonos(contract)


def is_aragonos_reentrancy_guard(contract: "Contract") -> bool:
    return contract.name == "ReentrancyGuard" and is_aragonos(contract)


def is_aragonos_time_helpers(contract: "Contract") -> bool:
    return contract.name == "TimeHelpers" and is_aragonos(contract)


def is_aragonos_vault_recoverable(contract: "Contract") -> bool:
    return contract.name == "VaultRecoverable" and is_aragonos(contract)
