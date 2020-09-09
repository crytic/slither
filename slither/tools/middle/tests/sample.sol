contract Contract {
    function f(int x) public returns (int) {
        if (x > 0) {
            return 1 + f(x-1);
        }
        return x;
    }
}
