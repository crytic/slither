contract Test {
    struct UserDefined {
        uint256 a;
        string b;
    }

    event Val(uint, uint);
    event Val2(UserDefined, UserDefined);

    function f(uint a, uint b) public {
        emit Val(a, b);
    }

    function f2(UserDefined memory a, UserDefined memory b) public {
        emit Val2(a, b);
    }
}

contract D {
    struct UserDefined {
        uint256 a;
        string b;
    }

    struct badUserDefined {
        string a;
        uint256 b;
    }

    function bad_numArgs() public {
        Test t = new Test();
        address(t).call(abi.encodeWithSelector(Test.f.selector, "test"));
    }

    function bad_elementaryTypes() public {
        Test t = new Test();
        address(t).call(
            abi.encodeWithSelector(Test.f.selector, "test", "test")
        );
    }

    function bad_userDefined() public {
        Test t = new Test();
        address(t).call(
            abi.encodeWithSelector(
                Test.f2.selector,
                badUserDefined({a: "test", b: 1}),
                badUserDefined({a: "test", b: 1})
            )
        );
    }

    function good() public {
        Test t = new Test();
        address(t).call(abi.encodeWithSelector(Test.f.selector, 1, 2));
    }
}
