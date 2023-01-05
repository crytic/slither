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

    function bad1() public {
        token.safeApprove(address(this), 0);
    }

    function bad2() public {
        SafeERC20.safeApprove(token, address(this), 0);
    }
}
