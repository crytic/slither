from pathlib import Path


libraries = {
    'Openzeppelin-SafeMath': lambda x: is_openzepellin_safemath(x),
    'Openzeppelin-ECRecovery': lambda x: is_openzepellin_ecrecovery(x),
    'Openzeppelin-Ownable': lambda x: is_openzepellin_ownable(x),
    'Openzeppelin-ERC20': lambda x: is_openzepellin_erc20(x),
    'Openzeppelin-ERC721': lambda x: is_openzepellin_erc721(x),
    'Zos-Upgrade': lambda x: is_zos_initializable(x),
    'Dapphub-DSAuth': lambda x: is_dapphub_ds_auth(x),
    'Dapphub-DSMath': lambda x: is_dapphub_ds_math(x),
    'Dapphub-DSToken': lambda x: is_dapphub_ds_token(x),
    'Dapphub-DSProxy': lambda x: is_dapphub_ds_proxy(x),
    'Dapphub-DSGroup': lambda x: is_dapphub_ds_group(x),
    'AragonOS-App': lambda x: is_aragonos_app(x)
}

def is_standard_library(contract):
    for name, is_lib in libraries.items():
        if is_lib(contract):
            return name
    return None


###################################################################################
###################################################################################
# region General libraries
###################################################################################
###################################################################################


def is_openzepellin(contract):
    if not contract.is_from_dependency():
        return False
    return 'openzeppelin-solidity' in Path(contract.source_mapping['filename_absolute']).parts


def is_zos(contract):
    if not contract.is_from_dependency():
        return False
    return 'zos-lib' in Path(contract.source_mapping['filename_absolute']).parts


def is_aragonos(contract):
    if not contract.is_from_dependency():
        return False
    return '@aragon/os' in Path(contract.source_mapping['filename_absolute']).parts


# endregion
###################################################################################
###################################################################################
# region SafeMath
###################################################################################
###################################################################################


def is_safemath(contract):
    return contract.name == "SafeMath"


def is_openzepellin_safemath(contract):
    return is_safemath(contract) and is_openzepellin(contract)

# endregion
###################################################################################
###################################################################################
# region ECRecovery
###################################################################################
###################################################################################


def is_ecrecovery(contract):
    return contract.name == 'ECRecovery'


def is_openzepellin_ecrecovery(contract):
    return is_ecrecovery(contract) and is_openzepellin(contract)


# endregion
###################################################################################
###################################################################################
# region Ownable
###################################################################################
###################################################################################


def is_ownable(contract):
    return contract.name == 'Ownable'


def is_openzepellin_ownable(contract):
    return is_ownable(contract) and is_openzepellin(contract)


# endregion
###################################################################################
###################################################################################
# region ERC20
###################################################################################
###################################################################################


def is_erc20(contract):
    return contract.name == 'ERC20'


def is_openzepellin_erc20(contract):
    return is_erc20(contract) and is_openzepellin(contract)


# endregion
###################################################################################
###################################################################################
# region ERC721
###################################################################################
###################################################################################


def is_erc721(contract):
    return contract.name == 'ERC721'


def is_openzepellin_erc721(contract):
    return is_erc721(contract) and is_openzepellin(contract)


# endregion
###################################################################################
###################################################################################
# region Zos Initializable
###################################################################################
###################################################################################


def is_initializable(contract):
    return contract.name == 'Initializable'


def is_zos_initializable(contract):
    return is_initializable(contract) and is_zos(contract)


# endregion
###################################################################################
###################################################################################
# region DappHub
###################################################################################
###################################################################################

dapphubs = {
    'DSAuth': 'ds-auth',
    'DSMath': 'ds-math',
    'DSToken': 'ds-token',
    'DSProxy': 'ds-proxy',
    'DSGroup': 'ds-group',
}


def _is_ds(contract, name):
    return contract.name == name

def _is_dappdhub_ds(contract, name):
    if not contract.is_from_dependency():
        return False
    if not dapphubs[name] in Path(contract.source_mapping['filename_absolute']).parts:
        return False
    return _is_ds(contract, name)

def is_ds_auth(contract):
    return _is_ds(contract, 'DSAuth')

def is_dapphub_ds_auth(contract):
    return _is_dappdhub_ds(contract, 'DSAuth')

def is_ds_math(contract):
    return _is_ds(contract, 'DSMath')

def is_dapphub_ds_math(contract):
    return _is_dappdhub_ds(contract, 'DSMath')

def is_ds_token(contract):
    return _is_ds(contract, 'DSToken')

def is_dapphub_ds_token(contract):
    return _is_dappdhub_ds(contract, 'DSToken')

def is_ds_proxy(contract):
    return _is_ds(contract, 'DSProxy')

def is_dapphub_ds_proxy(contract):
    return _is_dappdhub_ds(contract, 'DSProxy')

def is_ds_group(contract):
    return _is_ds(contract, 'DSGroup')

def is_dapphub_ds_group(contract):
    return _is_dappdhub_ds(contract, 'DSGroup')

# endregion
###################################################################################
###################################################################################
# region Aragon
###################################################################################
###################################################################################

def is_aragonos_app(contract):
    return contract.name == "AragonApp" and is_aragonos(contract)
