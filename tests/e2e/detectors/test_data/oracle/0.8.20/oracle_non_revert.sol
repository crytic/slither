// SPDX-License-Identifier: MIT

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

    function check_timestamp(uint256 updatedAt) internal view returns (bool) {
        if (updatedAt - block.timestamp < 500) {
            return true;
        }
        return false;
    }

    function check_roundID(
        uint80 roundID,
        uint80 answeredInRound
    ) internal pure returns (bool) {
        if (answeredInRound > roundID) {
            return true;
        }
        return false;
    }

    function oracle_call() internal view returns (bool, uint256) {
        (
            uint80 roundID,
            int256 price,
            ,
            uint256 updatedAt,
            uint80 answeredInRound
        ) = priceFeedDAIETH.latestRoundData();
        bool errorPrice = price_check(price);
        if (
            errorPrice == false ||
            check_timestamp(updatedAt) == false ||
            check_roundID(roundID, answeredInRound) == false
        ) {
            return (false, 0);
        }

        return (true, uint256(price));
    }

    function getPriceUSD() external view returns (uint256) {
        (bool problem, uint price) = oracle_call();
        require(problem);
        return price;
    }
}
