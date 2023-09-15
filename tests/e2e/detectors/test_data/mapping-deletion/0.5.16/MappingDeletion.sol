// pragma solidity ^0.4.24;

library Lib{

    struct MyStruct{
        mapping(address => uint) maps;
    }

    function deleteSt(MyStruct[1] storage st) internal {
        delete st[0];
    }

}

contract Balances {
    
    struct BalancesStruct{
        address owner;
        mapping(address => uint) balances;
    }

    struct NestedBalanceStruct {
        BalancesStruct balanceStruct;
    }
    
    mapping(uint => BalancesStruct) public stackBalance;
    NestedBalanceStruct internal nestedStackBalance;

    function createBalance(uint idx) public {
        require(stackBalance[idx].owner == address(0));
        BalancesStruct storage str = stackBalance[idx];
        str.owner = msg.sender;
    }    
    
    function deleteBalance(uint idx) public {
        require(stackBalance[idx].owner == msg.sender);
        delete stackBalance[idx];
    }

    function deleteNestedBalance() public {
        delete nestedStackBalance;
    }
    
    function setBalance(uint idx, address addr, uint val) public {
        require(stackBalance[idx].owner == msg.sender);
        
        stackBalance[idx].balances[addr] = val;
    }
    
    function getBalance(uint idx, address addr) public view returns(uint){
        return stackBalance[idx].balances[addr];
    }
    
}
