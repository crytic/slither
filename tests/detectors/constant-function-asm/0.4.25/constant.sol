contract Constant {
   
    uint a;
    
    function test_view_bug() public view{
        a = 0;
    }
    
    function test_constant_bug() public constant{
        a = 0;
    }

    function test_view_shadow() public view{
        uint a;
        a = 0;
    }

    function test_view() public view{
        a;
    }

    function test_assembly_bug() public view{
        assembly{}
    }
}
