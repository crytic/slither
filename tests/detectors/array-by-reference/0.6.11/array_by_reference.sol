contract C {
    uint[1] public x;

    function f() public {
        setByRef(x); // can set x.
        setByValue(x); // cannot set x.
        uint test = 1 + setByValueAndReturn(x); // cannot set x.
    }

    function g() public {
        uint[1] storage y = x;
        setByRef(y); // can set y.
        setByValue(y); // cannot set y.
        uint test = 1 + setByValueAndReturn(y); // cannot set y.
    }

    function setByRef(uint[1] storage arr) internal {
        arr[0] = 1;
    }

    function setByValue(uint[1] memory arr) public {
        arr[0] = 2;
    }

    function setByValueAndReturn(uint[1] memory arr) public returns(uint) {
        arr[0] = 2;
        return arr[0];
    }
}

contract D {
    // Struct definition
    struct TestStruct {
        uint[1] x;
    }

    // State Variables
    TestStruct ts;
    uint[1] x;

    // Functions
    function f() public {
        C c = new C();
        c.setByValue(ts.x); // cannot set x.
        uint test = 1 + c.setByValueAndReturn(ts.x); // cannot set x.
        c.setByValue(x); // cannot set x.
        test = 1 + c.setByValueAndReturn(x); // cannot set x.
    }


}