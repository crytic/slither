// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

interface AggregatorV3Interface {
    function decimals() external view returns (uint8);

    function description() external view returns (string memory);

    function version() external view returns (uint256);

    // getRoundData and latestRoundData should both raise "No data present"
    // if they do not have data to report, instead of returning unset values
    // which could be misinterpreted as actual reported values.
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

contract ChainlinkETHUSDPriceConsumer {
    AggregatorV3Interface internal priceFeed;

    constructor() public {
        priceFeed = AggregatorV3Interface(
            0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419
        );
    }
    /**
     * Returns the latest price. Ensures the price is not outdated by checking the `updatedAt` timestamp.
     */
    function getLatestPrice() public view returns (int) {
        (, int price, , uint256 updateAt, ) = priceFeed.latestRoundData();
        uint current_timestamp = block.timestamp;
        require(current_timestamp - updateAt < 1 minutes, "Price is outdated");
        return price;
    }

    function getDecimals() public view returns (uint8) {
        return priceFeed.decimals();
    }
}
