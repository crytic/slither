
contract VarReadUsingThis {
    address public erc20;
    mapping(uint => address) public myMap;
    function bad1(uint x) external returns(address) {
        return this.myMap(x);
    }
    function bad2() external returns(address) {
        return this.erc20();
    }
    function bad3() external returns(address) {
        if (this.erc20() == address(0)) revert();
    }
    function bad4() internal returns(address) {
        for (uint x; x < 10; x++) {
            address local = this.erc20();
        } 
    }
    function good1(uint x) external returns(address) {
        return myMap[x];
    }
    function good2() external returns(address) {
        return erc20;
    }
    function good3() external returns(address) {
        if (erc20 == address(0)) revert();
    }
    function good4() internal returns(address) {
        for (uint x; x < 10; x++) {
            address local = erc20;
        } 
    }    
    function mapExternal(uint x) external view returns(address) {
        return myMap[x];
    }
    function good5(uint x) external returns(address) {
        this.mapExternal(x);
    }
}
