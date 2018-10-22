pragma solidity ^0.4.24;

import "./external_function_test_2.sol";

contract ItemTwo is ItemFour {
    function helloTwo() public {
        uint256 i = 0;
    }
}

contract ItemThree {

    function helloThree() public {

    }

    function helloTwo() public {

    }

    function helloOne() public {

    }

    function my_func() internal returns(bool){
        return true;
    }

}

contract ItemOne is ItemTwo {
    function helloOne() public {
        uint256 i = 0;
        address three = new ItemThree();
        three.call(bytes4(keccak256("helloTwo()")));
        super.helloTwo();
        ItemFour four = new ItemFour();
        four.helloFour();
    }
}

contract InternalCall {
    
    function() returns(uint) ptr;
    
    function set_test1() external{
        ptr = test1;
    }
    
    function set_test2() external{
        ptr = test2;
    }
    
    function test1() public returns(uint){
        return 1;
    }
    
    function test2() public returns(uint){
        return 2;
    }
    
    function test3() public returns(uint){
        return 3;
    }
    
    function exec() external returns(uint){
        return ptr();
    }
    
}