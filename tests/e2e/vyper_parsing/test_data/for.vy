

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

struct X:
    y: int8

strategies: public(DynArray[address, MAX_QUEUE])

@external
def for_loop():

    for strategy in self.strategies:
        z: address = IStrategy(strategy).asset()

