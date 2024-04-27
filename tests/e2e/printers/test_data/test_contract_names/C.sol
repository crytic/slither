import "./A.sol";

contract C is A {
    function c_main() public pure {
        a_main();
    }
}
