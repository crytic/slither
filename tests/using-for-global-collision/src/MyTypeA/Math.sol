import "./Type.sol";

function mul(MyTypeA a, MyTypeA b) pure returns (MyTypeA) {
    return MyTypeA.wrap(MyTypeA.unwrap(a) * MyTypeA.unwrap(b));
}
