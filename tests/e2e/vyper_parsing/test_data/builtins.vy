
@payable
@external
def test_builtins():
    a: address = block.coinbase
    b: uint256 = block.difficulty
    c: uint256 = block.prevrandao
    d: uint256 = block.number
    e: bytes32 = block.prevhash
    f: uint256 = block.timestamp
    h: bytes32 = convert(chain.id, bytes32)
    i: Bytes[32] = slice(msg.data, 0, 32)
    j: uint256 = msg.gas
    k: address = msg.sender
    l: uint256 = msg.value
    m: address = tx.origin
    n: uint256 = tx.gasprice
    x: uint256 = self.balance
    send(msg.sender, x)

@external
def c(x: uint256):
    user_shares: DynArray[uint256, 10] = []
    user_shares.append(1)
    user_shares.pop()
