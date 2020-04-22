contract C{

    struct St{
        uint one;
        uint two;
    }
    
    struct Nested{
        St s;
    }

    mapping(uint => Nested) map;


    St st1;
    St st2;
    uint ret;
    uint ret2;
    Nested n;

    mapping(uint => uint) map2;

    mapping(uint => St) sts;

    struct NestedNested{
        mapping(uint => Nested) mn;
    }
    NestedNested nestednested;


    function g(uint a) public{
        map[0].s.one = a;
        map[0].s.two = map[0].s.one;
    }


    function f(uint a) public{
        st1.one = a;
        st2 = st1;
        ret = st2.one;
    }

    function t(uint a) public{
        map2[0] = a;
        ret2 = map2[0];
    }


    function i(uint b) public{
        st1.one = b;
        sts[0].one = b;
    }


    function j(uint a) public{
        n.s.one = a;
        n.s.two = n.s.one;
    }

    function k(uint a, uint b) public{
        nestednested.mn[0].s.one = a;
        nestednested.mn[0].s.two = nestednested.mn[0].s.one + b;
    }

    // Test inter transational
    function f1(uint x) public{
        n.s.one = x;
    }

    function f2(uint x) public{
        n.s.two = n.s.one;
    }



}
