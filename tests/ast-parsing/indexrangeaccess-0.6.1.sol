contract C {
    function f(bytes calldata x) external {
        x[:4];
        x[4:];

        x[0:4];

        x[:];
    }
}