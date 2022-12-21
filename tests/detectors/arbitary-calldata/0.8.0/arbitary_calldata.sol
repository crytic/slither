contract A {
    function permit(address token, bytes calldata data) public {
        (bool success, ) = token.call(data);
        require(success, "failure of call()");
    }
}