contract Test {
    struct UserDefined {
        uint256 a;
        string b;
    }

    event Val(uint, uint);
    event Val2(UserDefined, UserDefined);
    event Val3(uint256[]);

    function f(uint a, uint b) public {
        emit Val(a, b);
    }

    function f2(UserDefined memory a, UserDefined memory b) public {
        emit Val2(a, b);
    }

    function f3(uint256[] memory a) public {
        emit Val3(a);
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

    function bad_array() public {
        Test t = new Test();
        uint32[] memory arr = new uint32[](2);
        arr[0] = 1;
        arr[1] = 2;
        address(t).call(abi.encodeWithSelector(Test.f3.selector, arr));
    }

    function good() public {
        Test t = new Test();
        address(t).call(abi.encodeWithSelector(Test.f.selector, 1, 2));
    }

    function good_array() public {
        Test t = new Test();
        uint256[] memory arr = new uint256[](2);
        arr[0] = 1;
        arr[1] = 2;
        address(t).call(abi.encodeWithSelector(Test.f3.selector, arr));
    }
}
