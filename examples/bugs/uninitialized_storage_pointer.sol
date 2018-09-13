contract Uninitialized{

    struct St{
        uint a;
    }

    function func() payable{
        St st;
        St memory st2;
    }    

}
