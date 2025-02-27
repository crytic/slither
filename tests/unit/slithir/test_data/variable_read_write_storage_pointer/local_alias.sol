contract Test{

    struct S{
        uint a;
    }

    S s0;
    S s1;

    function test() public{
        S storage s_local = s0;

        if(true){
            s_local = s1;
        }

        s_local.a = 10;

    }
}