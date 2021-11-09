pragma solidity 0.5.16;

contract A{
    uint256 public num;
    function getNum() view public returns(uint256){
        return num;
    }
}

contract B is A{
    constructor(uint256 _num) public{
        num = _num;
    }
}

contract C is A{
    function setNum() public{
        num += 10;
    }
}

contract D is C{
    function getNum() view public returns(uint256){
        return num + 10;
    }
}

/*
Now, you want getNum in C, but you end up with getNum 
in A because you specified the wrong inheritance order.
(A is the last one)
*/

//Solidity supports multiple inheritance, and when you have a function or variable of the same name in your base class, the order of inheritance matters, which determines which one will be integrated into the subclass. The wrong inheritance sequence will result in the functionality of the contract not being what the developer expected.
contract E is D, B{
    address public owner;
    constructor() public{
        owner = msg.sender;
    }
}
