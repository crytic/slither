contract C {
    mapping(uint => uint) m;

    function f() public {
        uint a;

        a++;
        a--;
        ++a;
        --a;
        ~a;

        int i;
        i = -5;

        delete m[0];

        bool b;
        !b;
    }
}