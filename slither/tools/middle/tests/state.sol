contract State {
    int state = 0;
    function f() public returns (int) {
            g();
            return state;
    }

    function g() public {
            h();
    }

    function h() public {
            state = state + 1;
    }
}