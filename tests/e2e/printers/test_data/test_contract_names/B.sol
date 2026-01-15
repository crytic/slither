import "./A.sol";

contract B is A {
    function b_main() public pure {
        a_main();
    }
}

