

interface ERC20:
    def totalSupply() -> uint256: view
    def balanceOf(_owner: address) -> uint256: view
    def allowance(_owner: address, _spender: address) -> uint256: view
    def transfer(_to: address, _value: uint256) -> bool: nonpayable
    def transferFrom(_from: address, _to: address, _value: uint256) -> bool: nonpayable
    def approve(_spender: address, _value: uint256) -> bool: nonpayable
