contract Scope{

    function nested_scope() public{
        uint a;
        {
            uint b;
            {
                uint c;
            }
        }

    }

    function if_scope() public{
        if(true)
        {
            uint a;
        }
        else{
            uint b;
        }
    }

    function while_scope() public{
        uint a;
        while(true)
        {
            uint b;
        }
    }
    function for_scope() public{
        uint a;
        for(uint b; b < 10; b++)
        {
            uint c;
        }
    }
}
