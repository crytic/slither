pragma solidity >=0.4.22 <0.6.0;
contract test{
    uint a;
    constructor()public{
        a =5;
    }
    
}
contract test2 is test{
    constructor()public{
        a=10;
    }
}
contract test3 is test2{
    address owner;
    bytes32 name;
    constructor(bytes32 _name)public{
        owner = msg.sender;
        name = _name;
        a=20;
    }
    function print() public returns(uint b){
        b=a;

    }
}