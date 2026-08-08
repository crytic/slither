pragma solidity 0.8.20;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);

    /**
     * @dev Moves a `value` amount of tokens from the caller's account to `to`.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transfer(address to, uint256 value) external returns (bool);

    function decimals() external view virtual returns (uint8);
}
interface IUniswapV2Pair {
    function getReserves()
        external
        view
        returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
}
interface IUniswapV2Factory {
    function getPair(
        address tokenA,
        address tokenB
    ) external view returns (address pair);
}

interface IUniswapV2Router01 {
    function quote(
        uint amountA,
        uint reserveA,
        uint reserveB
    ) external pure returns (uint amountB);
    function getAmountOut(
        uint amountIn,
        uint reserveIn,
        uint reserveOut
    ) external pure returns (uint amountOut);
}

contract getAmountOut {
    // Same address just for testing purposes
    address UNISWAP_ROUTER =
        address(0x96871914D0F4354A79B1E4651b464351e093b737);
    address UNISWAP_FACTORY =
        address(0x96871914D0F4354A79B1E4651b464351e093b737);
    address USDC = address(0x96871914D0F4354A79B1E4651b464351e093b737);
    address WETH = address(0x96871914D0F4354A79B1E4651b464351e093b737);

    function getEthUsdPrice() public view returns (uint256) {
        address pairAddress = IUniswapV2Factory(UNISWAP_FACTORY).getPair(
            USDC,
            WETH
        );
        require(pairAddress != address(0x00), "pair not found");
        IUniswapV2Pair pair = IUniswapV2Pair(pairAddress);
        (uint256 left, uint256 right, ) = pair.getReserves();
        (uint256 usdcReserves, uint256 ethReserves) = (USDC < WETH)
            ? (left, right)
            : (right, left);
        uint8 ethDecimals = IERC20(WETH).decimals();
        //uint8 usdcDecimals = ERC20(USDC).decimals();
        //returns price in 6 decimals
        return
            IUniswapV2Router01(UNISWAP_ROUTER).getAmountOut(
                10 ** ethDecimals,
                ethReserves,
                usdcReserves
            );
    }
}
