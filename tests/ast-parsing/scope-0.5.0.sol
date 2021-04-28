contract Scope{

    function nested_scope() public{
        uint a;
        {
            uint a;
            {
                uint a;
            }
        }

    }

    function if_scope() public{
        if(true)
        {
            uint a;
        }
        else{
            uint a;
        }
    }

    function while_scope() public{
        uint a;
        while(true)
        {
            uint a;
        }
    }
    function for_scope() public{
        uint a;
        for(uint a; a < 10; a++)
        {
            uint a;
        }
    }
}
