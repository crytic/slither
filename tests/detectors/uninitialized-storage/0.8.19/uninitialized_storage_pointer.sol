contract Uninitialized{

    struct St{
        uint a;
    }

    function test() internal returns (St storage ret){
        ret =  ret;
        ret.a += 1;
    }    

}
