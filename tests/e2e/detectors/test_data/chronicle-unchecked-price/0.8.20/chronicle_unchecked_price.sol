interface IChronicle {
    /// @notice Returns the oracle's current value.
    /// @dev Reverts if no value set.
    /// @return value The oracle's current value.
    function read() external view returns (uint value);

    /// @notice Returns the oracle's current value and its age.
    /// @dev Reverts if no value set.
    /// @return value The oracle's current value.
    /// @return age The value's age.
    function readWithAge() external view returns (uint value, uint age);

    /// @notice Returns the oracle's current value.
    /// @return isValid True if value exists, false otherwise.
    /// @return value The oracle's current value if it exists, zero otherwise.
    function tryRead() external view returns (bool isValid, uint value);

    /// @notice Returns the oracle's current value and its age.
    /// @return isValid True if value exists, false otherwise.
    /// @return value The oracle's current value if it exists, zero otherwise.
    /// @return age The value's age if value exists, zero otherwise.
    function tryReadWithAge()
        external
        view
        returns (bool isValid, uint value, uint age);
}

interface IScribe is IChronicle {
    /// @notice Returns the oracle's latest value.
    /// @dev Provides partial compatibility with Chainlink's
    ///      IAggregatorV3Interface.
    /// @return roundId 1.
    /// @return answer The oracle's latest value.
    /// @return startedAt 0.
    /// @return updatedAt The timestamp of oracle's latest update.
    /// @return answeredInRound 1.
    function latestRoundData()
        external
        view
        returns (
            uint80 roundId,
            int answer,
            uint startedAt,
            uint updatedAt,
            uint80 answeredInRound
        );

    /// @notice Returns the oracle's latest value.
    /// @dev Provides partial compatibility with Chainlink's
    ///      IAggregatorV3Interface.
    /// @custom:deprecated See https://docs.chain.link/data-feeds/api-reference/#latestanswer.
    /// @return answer The oracle's latest value.
    function latestAnswer() external view returns (int);
}

contract C {
    IScribe scribe;
    IChronicle chronicle;

    constructor(address a) {
        scribe = IScribe(a);
        chronicle = IChronicle(a);
    }

    function bad() public {
        uint256 price = chronicle.read();
    }

    function good() public {
        uint256 price = chronicle.read();
        require(price != 0);
    }

    function bad2() public {
        (uint256 price,) = chronicle.readWithAge();
    }

    function good2() public {
        (uint256 price,) = chronicle.readWithAge();
        require(price != 0);
    }

    function bad3() public {
        (bool isValid, uint256 price) = chronicle.tryRead();
    }

    function good3() public {
        (bool isValid, uint256 price) = chronicle.tryRead();
        require(isValid);
    }

    function bad4() public {
        (bool isValid, uint256 price,) = chronicle.tryReadWithAge();
    }

    function good4() public {
        (bool isValid, uint256 price,) = chronicle.tryReadWithAge();
        require(isValid);
    }

    function bad5() public {
        int256 price = scribe.latestAnswer();
    }

    function good5() public {
        int256 price = scribe.latestAnswer();
        require(price != 0);
    }

    function bad6() public {
        (, int256 price,,,) = scribe.latestRoundData();
    }

    function good6() public {
        (, int256 price,,,) = scribe.latestRoundData();
        require(price != 0);
    }

}