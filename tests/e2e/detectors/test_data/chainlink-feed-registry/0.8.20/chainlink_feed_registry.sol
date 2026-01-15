interface FeedRegistryInterface {
  function latestRoundData(
    address base,
    address quote
  ) external view returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound);
}

interface MyInterface {
  function latestRoundData(
    address base,
    address quote
  ) external view returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound);
}

contract A {
    FeedRegistryInterface public immutable registry;
    MyInterface public immutable my_interface;

    constructor(FeedRegistryInterface _registry, MyInterface _my_interface) {
        registry = _registry;
        my_interface = _my_interface;
    }

    function getPriceBad(address base, address quote) public returns (uint256) {
        (, int256 price,,,) = registry.latestRoundData(base, quote);
        // Do price validation
        return uint256(price);
    }

    function getPriceGood(address base, address quote) public returns (uint256) {
        (, int256 price,,,) = my_interface.latestRoundData(base, quote);
        // Do price validation
        return uint256(price);
    }


}