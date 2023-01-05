interface IERC20 {}

library SafeERC20 {
    function safeApprove(
        IERC20 token,
        address spender,
        uint256 value
    ) internal {}
}

contract C {
    using SafeERC20 for IERC20;
    IERC20 token;
    uint256 zero = 0;

    function good1() public {
        token.safeApprove(address(this), 0);
    }

    function good2() public {
        SafeERC20.safeApprove(token, address(this), 0);
    }

    function good3() public {
        token.safeApprove(address(this), zero);
    }

    function good4(uint256 value) public {
        token.safeApprove(address(this), 0);
        good4(value);
    }

    function bad1() public {
        token.safeApprove(address(this), type(uint256).max);
    }

    function bad2() public {
        SafeERC20.safeApprove(token, address(this), type(uint256).max);
    }

    function bad3(uint256 value) public {
        token.safeApprove(address(this), value);
    }
}
