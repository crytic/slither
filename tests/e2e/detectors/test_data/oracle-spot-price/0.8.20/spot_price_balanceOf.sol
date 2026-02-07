pragma solidity 0.8.20;

interface IERC20 {
    event Transfer(address indexed from, address indexed to, uint256 value);

    event Approval(
        address indexed owner,
        address indexed spender,
        uint256 value
    );

    function totalSupply() external view returns (uint256);

    function balanceOf(address account) external view returns (uint256);

    function transfer(address to, uint256 value) external returns (bool);

    function allowance(
        address owner,
        address spender
    ) external view returns (uint256);

    function approve(address spender, uint256 value) external returns (bool);

    function transferFrom(
        address from,
        address to,
        uint256 value
    ) external returns (bool);
}

contract BalanceOfData {
    function getPriceV2(
        address pool,
        address USDCAddress,
        address weth
    ) internal view returns (uint256 price) {
        uint256 usdcBalance = IERC20(USDCAddress).balanceOf(pool);
        uint256 ethBalance = IERC20(weth).balanceOf(pool);

        price = (ethBalance * 10 ** 18) / usdcBalance;
    }
}
