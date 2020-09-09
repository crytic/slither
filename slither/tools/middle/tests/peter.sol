pragma solidity >=0.4.16 <0.7.0;
contract Contract {
    int state = 0;

    function f() public returns (int) {
        if (state == 0) {
            state += 1;
        }
        return state;
    }
}