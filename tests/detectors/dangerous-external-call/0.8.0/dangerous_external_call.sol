interface IERC20 {
    function safeTransferFrom (address, address, uint) external;
}
contract A {
    function depositFor(address token, uint _amount,address user ) public {
        IERC20(token).safeTransferFrom(msg.sender, address(this), _amount); //vulnerable point
    }
}