contract Test {
    function myVirtualFunction() virtual external {
    }
}

contract A is Test {
    function myVirtualFunction() virtual override external {
    }
}

contract B is A {
    function myVirtualFunction() override external {
    }

}

contract C is Test {
    function myVirtualFunction() override external {
    }
}

contract X is Test {
    function myVirtualFunction() virtual override external {
    }
}

contract Y {
    function myVirtualFunction() virtual external {
    }
}

contract Z is Y, X{
    function myVirtualFunction() virtual override(Y, X) external {
    }
}


abstract contract Name {
    constructor() {
        
    }
}

contract Name2 is Name {
    constructor() {
        
    }
}

abstract contract Test2 {
    function f() virtual public;
}

contract A2 is Test2 {
    function f() virtual override public {
    }
}

abstract contract I {
 function a() public virtual {}
}
contract J is I {}
contract K is J {
 function a() public override {}
}