pragma solidity ^0.4.24;

library UnsafeMath{

    function add(uint a, uint b) public pure returns(uint){
        return a + b;
    }

    function min(uint a, uint b) public pure returns(uint){
        return a - b;
    }
}

contract MyContract{
    using UnsafeMath for uint;

    mapping(address => uint) balances;

    function transfer(address to, uint val) public{

        balances[msg.sender] = balances[msg.sender].min(val);
        balances[to] = balances[to].add(val);

    }


}
