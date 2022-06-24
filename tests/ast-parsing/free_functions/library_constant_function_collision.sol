library ExtendedMath {
    uint256 constant decimals = 18;
}

interface IERC20 {
    function decimals() external view returns (uint8);
}

contract A {
    using ExtendedMath for *;
    function test(address x) public {
        uint8 decimals = IERC20(address(x)).decimals();
    }
}
