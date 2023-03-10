contract Uninitialized{

    struct St{
        uint a;
    }

    function bad() internal returns (St storage ret){
        ret =  ret;
        ret.a += 1;
    }    

    function ok(St storage ret) internal {
        ret = ret;
        ret.a += 1;
    }    

}
