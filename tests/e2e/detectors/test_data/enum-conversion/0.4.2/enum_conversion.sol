pragma solidity 0.4.2;
    contract Test{
    
    enum E{a}
    
    function bug(uint a) public returns(E){
        return E(a);   
    }
}