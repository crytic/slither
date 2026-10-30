import "./A.sol";

interface MyInterfaceY {
    function ping() external;
}

// Intentionally list the interface first to ensure the inheritance-graph printer
// respects the interface filtering logic (see issue #2150).
contract D is MyInterfaceY, A {
    function ping() external override {}
}
