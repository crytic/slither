contract Uninitialized{

    function func() external returns(uint){
        uint uint_not_init;
        uint uint_init = 1;
        return uint_not_init + uint_init;
    }    

    function noreportfor() public {
        for(uint i; i < 6; i++) { 
            uint a = i;
        }
    }

}
