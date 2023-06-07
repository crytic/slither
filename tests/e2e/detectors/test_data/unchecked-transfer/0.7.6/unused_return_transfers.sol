contract Token {
    function transfer(address _to, uint256 _value) public returns (bool success) {
        return true;
    }
    function transferFrom(address _from, address _to, uint256 _value) public returns (bool success) {
        return true;
    }
    function other() public returns (bool) {
        return true;
    }
}
contract C {
    Token t;
    
    constructor() public {
        t = new Token();
    }

    // calling the transfer function
    function bad0() public{
        t.transfer(address(0), 1 ether);
    }
    function good0() public{
        bool a = t.transfer(address(0), 1 ether);
    }
    function good1() public{
        require(t.transfer(address(0), 1 ether), "failed");
    }
    function good2() public{
        assert(t.transfer(address(0), 1 ether));
    }
    function good3() public returns (bool) {
        return t.transfer(address(0), 1 ether);
    }
    function good4() public returns (bool ret) {
        ret = t.transfer(address(0), 1 ether);
    }

    // calling the transferFrom function
    function bad1() public {
        t.transferFrom(address(this), address(0), 1 ether);
    }
    function good5() public{
        bool a = t.transferFrom(address(this), address(0), 1 ether);
    }
    function good6() public{
        require(t.transferFrom(address(this), address(0), 1 ether), "failed");
    }
    function good7() public{
        assert(t.transferFrom(address(this), address(0), 1 ether));
    }
    function good8() public returns (bool) {
        return t.transferFrom(address(this), address(0), 1 ether);
    }
    function good9() public returns (bool ret) {
        ret = t.transferFrom(address(this), address(0), 1 ether);
    }

    // calling the other function
    function good10() public {
        t.other();
    }
}