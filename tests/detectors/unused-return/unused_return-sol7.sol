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
    function good0() public{
        t.transfer(address(0), 1 ether);
    }
    function good1() public{
        bool a = t.transfer(address(0), 1 ether);
    }
    function good2() public{
        require(t.transfer(address(0), 1 ether), "failed");
    }
    function good3() public{
        assert(t.transfer(address(0), 1 ether));
    }
    function good4() public returns (bool) {
        return t.transfer(address(0), 1 ether);
    }
    function good5() public returns (bool ret) {
        ret = t.transfer(address(0), 1 ether);
    }

    // calling the transferFrom function
    function good6() public {
        t.transferFrom(address(this), address(0), 1 ether);
    }
    function good7() public{
        bool a = t.transferFrom(address(this), address(0), 1 ether);
    }
    function good8() public{
        require(t.transferFrom(address(this), address(0), 1 ether), "failed");
    }
    function good9() public{
        assert(t.transferFrom(address(this), address(0), 1 ether));
    }
    function good10() public returns (bool) {
        return t.transferFrom(address(this), address(0), 1 ether);
    }
    function good11() public returns (bool ret) {
        ret = t.transferFrom(address(this), address(0), 1 ether);
    }

    // calling the other function
    function bad0() public {
        t.other();
    }
    function good12() public{
        bool a = t.other();
    }
    function good13() public{
        require(t.other(), "failed");
    }
    function good14() public{
        assert(t.other());
    }
    function good15() public returns (bool) {
        return t.other();
    }
    function good16() public returns (bool ret) {
        ret = t.other();
    }
}