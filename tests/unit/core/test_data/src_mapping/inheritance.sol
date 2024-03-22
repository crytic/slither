contract A{

    function f() public virtual {

    }

    function test() public {
        f();
    }

}

contract B is A{

    function f() public override {

    }

}

contract C is A{

    function f() public override {

    }

    function test2() public {
        f();
    }

}

contract D is A{

}


type T is uint256;
uint constant U = 1;
error V(T);
event W(T);

contract E {
    type X is int256;
    function f() public {
        T t = T.wrap(U);
        if (T.unwrap(t) == 0) {
            revert V(t);
        }
        emit W(t);
        X x = X.wrap(1);
    }
}
