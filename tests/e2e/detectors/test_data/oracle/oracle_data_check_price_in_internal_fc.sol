interface AggregatorV3Interface {
    function decimals() external view returns (uint8);

    function description() external view returns (string memory);

    function version() external view returns (uint256);

    function getRoundData(
        uint80 _roundId
    )
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );

    function latestRoundData()
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );
}

contract StableOracleDAI {
    AggregatorV3Interface priceFeedDAIETH;

    constructor() {
        priceFeedDAIETH = AggregatorV3Interface(
            0x773616E4d11A78F511299002da57A0a94577F1f4
        );
    }

    function price_check(int price) internal pure returns (bool) {
        if (price > 0) {
            return true;
        }
        return false;
    }

    function getPriceUSD() external view returns (uint256) {
        uint256 wethPriceUSD = 1;
        uint256 DAIWethPrice = 1;

        // chainlink price data is 8 decimals for WETH/USD, so multiply by 10 decimals to get 18 decimal fractional
        //(uint80 roundID, int256 price, uint256 startedAt, uint256 timeStamp, uint80 answeredInRound) = priceFeedDAIETH.latestRoundData();
        (
            uint80 roundID,
            int256 price,
            ,
            uint256 updatedAt,
            uint80 answeredInRound
        ) = priceFeedDAIETH.latestRoundData();
        // bool val = price_check(price);
        require(price_check(price));
        require(updatedAt - block.timestamp < 500);
        require(answeredInRound > roundID);

        return
            (wethPriceUSD * 1e18) /
            ((DAIWethPrice + uint256(price) * 1e10) / 2);
    }
}
