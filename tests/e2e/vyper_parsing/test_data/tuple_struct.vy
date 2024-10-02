interface Test:
    def get() -> (uint80, int256, uint256, uint256, uint80): view
@external
def __default__() -> uint80:
    chainlink_lrd: (uint80, int256, uint256, uint256, uint80) = Test(msg.sender).get()
    return chainlink_lrd[0]




