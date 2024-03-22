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
