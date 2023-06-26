contract TernaryWithMax {
    function f(
        bool condition
    ) external returns(uint256 res) {
        res = type(uint256).max / (condition ? 10 : 1) ;
    }
}
