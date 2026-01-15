import "./A.sol";

interface MyInterfaceX {
    function count() external view returns (uint256);

    function increment() external;
}

contract C is A, MyInterfaceX {
    function c_main() public pure {
        a_main();
    }

    function count() external view override returns (uint256){
        return 1;
    }

    function increment() external override {

    }
}
