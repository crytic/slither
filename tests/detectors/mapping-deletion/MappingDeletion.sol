pragma solidity ^0.4.24;

library Lib{

    struct MyStruct{
        mapping(address => uint) maps;
    }

    function deleteSt(MyStruct[1] storage st){
        delete st[0];
    }

}

contract Balances {
    
    struct BalancesStruct{
        address owner;
        mapping(address => uint) balances;
    } 
    
    mapping(uint => BalancesStruct) public stackBalance;
    function createBalance(uint idx) public {
        require(stackBalance[idx].owner == 0);
        stackBalance[idx] = BalancesStruct(msg.sender);
    }    
    
    function deleteBalance(uint idx) public {
        require(stackBalance[idx].owner == msg.sender);
        delete stackBalance[idx];
    }
    
    function setBalance(uint idx, address addr, uint val) public {
        require(stackBalance[idx].owner == msg.sender);
        
        stackBalance[idx].balances[addr] = val;
    }
    
    function getBalance(uint idx, address addr) public view returns(uint){
        return stackBalance[idx].balances[addr];
    }
    
}
