pragma solidity 0.6.2;

//based on knowsec404

contract gray_Token {
    mapping(address => uint) public balances;
    uint public totalSupply;

    constructor(uint _initialSupply) public{
    balances[msg.sender] = totalSupply = _initialSupply;
    }
	
    function transfer(address _to, uint _value) public returns (bool) {
        require(balances[_to] >= _value);
        balances[_to] -= _value;
        
        require(balances[_to] + _value >= balances[_to]);
        balances[_to] += _value;
    }

    function balanceOf(address _owner) public view returns (uint balance) {
        return balances[_owner];
    }
}
