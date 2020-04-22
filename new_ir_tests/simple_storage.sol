contract A{
    
    struct St{
        uint x;
        uint y;
    }

    St st1;
    St st2;

    function set_x(St storage s, uint a) internal{
        s.x = a;
    }


    function set_y(St storage s, uint b) internal{
        s.y = b;
    }

    function test(uint param, uint param2) public{
        set_x(st1, param);
        set_y(st1, param2);
        st2.x = st1.x + st1.y;
    }

}
