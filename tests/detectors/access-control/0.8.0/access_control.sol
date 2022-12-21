contract A {
    address token;

    function setToken(address _token) public {
        token = _token;
    }
}