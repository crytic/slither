pragma solidity 0.6.2;

//based on knowsec404

contract Token {
    mapping(address => uint) public balances;
    uint public totalSupply;

    constructor(uint _initialSupply) public{
    balances[msg.sender] = totalSupply = _initialSupply;
    }

    function transfer(address _to, uint _value) public returns (bool) {
        //The following code can bypass the judgment by integer underflow
        //There are also integer overflow and underflow in Ethereum, and it will not throw an exception when overflow and underflow occur. If the overflow (underflow) result is related to the amount of money, it may cause serious economic loss, so developers need to deal with integer overflow (underflow) manually. The common method is to use the SafeMath library for integer operation, or you can manually check the result after integer operation.
        require(balances[msg.sender] - _value >= 0); 
        balances[msg.sender] -= _value;
        balances[_to] += _value;
        return true;
    }

    function balanceOf(address _owner) public view returns (uint balance) {
        return balances[_owner];
    }
}
