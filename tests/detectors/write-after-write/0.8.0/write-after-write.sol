contract Test{

    uint state;

    function read_state() internal returns(uint){
        return state;
    }

    function buggy_state() internal{
        state = 10;
        state = 20;
    }

    function not_buggy_state() internal{
        state = 10;
        read_state();
        state = 20;
    }

    function buggy_local() internal{
        uint a;
        a = 10;
        a = 20;
    }

    function not_buggy_if() internal{
        uint a = 0;
        if(true){
            a = 10;
        }
    }

    function not_buggy_loop() internal{

        for(uint i; i< 10; i++){
            uint a = 10;
        }
    }

    function not_bugy_ternary() internal{
        uint a = true? 1 : 0;
    }

    function not_bugy_external_state() internal{
        state = 10;
        address a;
        a.call("");
        state = 11;
    }

    function bugy_external_local() internal{
        uint local;
        local = 10;
        address a;
        a.call("");
        local = 11;
    }
}

