pragma solidity 0.4.25;

import "./external_function1.sol";

contract ItemTwo is ItemFour {
    function helloTwo() public {
        uint256 i = 0;
    }
}

contract ItemThree {

    function helloThree() {
    }

    function helloTwo() internal  {

    }

    function helloOne() public {

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