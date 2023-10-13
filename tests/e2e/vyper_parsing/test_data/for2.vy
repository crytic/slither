

x: constant(uint256) = 1 + 1
MAX_QUEUE: constant(uint256) = 1 + x

interface IStrategy:
    def asset() -> address: view
    def balanceOf(owner: address) -> uint256: view
    def maxDeposit(receiver: address) -> uint256: view
    def maxWithdraw(owner: address) -> uint256: view
    def withdraw(amount: uint256, receiver: address, owner: address) -> uint256: nonpayable
    def redeem(shares: uint256, receiver: address, owner: address) -> uint256: nonpayable
    def deposit(assets: uint256, receiver: address) -> uint256: nonpayable
    def totalAssets() -> (uint256): view
    def convertToAssets(shares: uint256) -> uint256: view
    def convertToShares(assets: uint256) -> uint256: view
    def previewWithdraw(assets: uint256) -> uint256: view

@external
def for_loop(strategies: DynArray[address, MAX_QUEUE]):
    _strategies: DynArray[address, MAX_QUEUE] = strategies

    for i in range(10):

        max_withdraw: uint256 = IStrategy(_strategies[i]).maxWithdraw(self)

