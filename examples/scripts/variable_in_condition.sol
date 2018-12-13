contract Contract{

    uint a;

    function condition() public{
        if(a==0){

        }
    }

    function call_require() public{
        require(a==0);
    }
    
    function read_and_write() public{
        a = a + 1;
    }

}
