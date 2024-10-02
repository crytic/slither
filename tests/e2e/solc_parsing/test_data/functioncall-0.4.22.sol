contract I {
    function I() public payable {}
}

contract C {
    struct S {
        uint a;
        uint b;
    }

    struct T {
        S s1;
        S s2;
    }

    function f() public payable {
        publicTarget();

        this.publicTarget();
        this.publicTarget.value(1 ether)();
        this.publicTarget.value(1 ether);
        this.publicTarget.gas(10000)();
        this.publicTarget.gas(10000).value(2 ether)();
        this.publicTarget.gas(10000).gas(20000).value(2 ether).gas(0)();

        internalTarget(1, 2);

        S({a: 5, b: 6});
        T({s1: S({a: 1, b: 2}), s2: S({a: 3, b: 4})});

        function(uint) external payable ptr;
        ptr.value(10 ether)(1);

        I(this);

        new I();
        (new I).value(1 ether)();

        abi.encode(1, 2, 3);
    }

    function publicTarget() public payable {

    }

    function internalTarget(uint a, uint b) public {

    }

    function cursed() public payable {
        var valuer = this.cursed.value;

        var value1Ether = valuer(1 ether);
        var value2Ether = valuer(2 ether);

        value1Ether();
        value1Ether();
        value2Ether();

        var deployer = new I;
        deployer();
        deployer();
    }
}