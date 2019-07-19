from slither.core.solidity_types.elementary_type import ElementaryType, ElementaryTypeName

base_type = {
    'timestamp': 'uint256',
    'timedelta': 'uint256',
    'wei_value': 'uint256'
}

def parse_type(str):
    if str in base_type:
        str = base_type[str]
    if str in ElementaryTypeName:
        return ElementaryType(str)