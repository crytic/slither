pragma solidity >=0.4.16 <0.7.0;

contract Contract {
    uint public a;

    function f(uint input) public returns(uint) {
        uint ret;
        if (input > 8) {
            ret = input;
        }
        ret = input + 3;
        return ret;
    }
}