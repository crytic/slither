import "./Type.sol";

function mul(MyTypeB a, MyTypeB b) pure returns (MyTypeB) {
    return MyTypeB.wrap(MyTypeB.unwrap(a) * MyTypeB.unwrap(b));
}

