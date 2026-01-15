import "./A.sol";

contract B is A {
    function b2_main() public pure {
        a_main();
    }
}
