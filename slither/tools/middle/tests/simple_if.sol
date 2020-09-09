pragma solidity >=0.4.16 <0.7.0;

contract SimpleIf {
    uint public a;

    function f(uint input) public {
        if(input == 2)
            a = 1;
        else
            a = 0;
    }
}