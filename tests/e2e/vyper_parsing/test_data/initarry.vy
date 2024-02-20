interface ERC20:
    def transfer(_to: address, _value: uint256) -> bool: nonpayable
    def transferFrom(_from: address, _to: address, _value: uint256) -> bool: nonpayable
    def approve(_spender: address, _value: uint256) -> bool: nonpayable

BORROWED_TOKEN: immutable(ERC20)
COLLATERAL_TOKEN: immutable(ERC20)

@external
def __init__(x: address, y: address):
    BORROWED_TOKEN = ERC20(x)
    COLLATERAL_TOKEN = ERC20(y)

@external
@pure
def coins(i: uint256) -> address:
    return [BORROWED_TOKEN.address, COLLATERAL_TOKEN.address][i]