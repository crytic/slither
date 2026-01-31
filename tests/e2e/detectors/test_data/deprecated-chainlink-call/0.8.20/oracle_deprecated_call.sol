pragma solidity 0.8.20;

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

    function latestAnswer() external view returns (int256);
}

contract Oracle {
    function getCurrentPrice(address _asset) external view returns (uint256) {
        AggregatorV3Interface aggregator = AggregatorV3Interface(_asset);
        int256 answer = aggregator.latestAnswer();
        require(
            answer > 0,
            "ChainlinkOracleManager: No pricing data available"
        );
    }
}
