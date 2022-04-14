type MyInt is uint;

contract B {
    type MyInt is int;

    function u() internal returns(int) {}

    function f() public{
        MyInt mi = MyInt.wrap(u());
    }
}

function f(MyInt a) pure returns (MyInt b) {
    b = MyInt(a);
}

contract D
{
    B.MyInt x = B.MyInt.wrap(int(1));
}

contract C {
    function f(Left[] memory a) internal returns(Left){
        return a[0];
    }
}
type Left is bytes2;

MyInt constant x = MyInt.wrap(20);

