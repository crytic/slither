pragma solidity ^0.4.24;

contract Token{
    function transfer(address to, uint value) returns(bool);
    function transferFrom(address from, address to, uint value) returns(bool);
}

contract Reentrancy {

    mapping(address => mapping(address => uint)) eth_deposed;
    mapping(address => mapping(address => uint)) token_deposed;

    function deposit_eth(address token) payable{
        eth_deposed[token][msg.sender] += msg.value;
    }

    function deposit_token(address token, uint value){
        token_deposed[token][msg.sender] += value;
        require(Token(token).transferFrom(msg.sender, address(this), value));
    }

    function withdraw(address token){
        msg.sender.transfer(eth_deposed[token][msg.sender]);
        require(Token(token).transfer(msg.sender, token_deposed[token][msg.sender]));

        eth_deposed[token][msg.sender] = 0;
        token_deposed[token][msg.sender] = 0;

    }

}
