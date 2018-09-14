contract Uninitialized{

    struct St{
        uint a;
    }

    function func() payable{
        St st; // non init, but never read so its fine
        St memory st2;
        St st_bug;
        st_bug.a;
    }    

}
