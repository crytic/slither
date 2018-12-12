contract Contract{

    uint a;

    function write() public{
        a++;
    }

    // shadowing of a
    function dont_write(uint a) public{
        a = a +1;
    }

}
