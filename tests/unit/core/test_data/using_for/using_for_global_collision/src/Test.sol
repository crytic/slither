import "./MyTypeB.sol";

contract UsingForGlobalTopLevelCollision {
    function mulAndUnwrap(MyTypeB x, MyTypeB y) external pure returns (uint256 z) {
        z = x.mul(y).unwrap();
    }
}