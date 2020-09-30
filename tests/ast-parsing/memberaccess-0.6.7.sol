contract I {

}

interface F {

}

contract C {
    struct S {
        uint a;
    }

    function f() public payable {
        uint[] memory x;
        x.length;

        C c;
        c.f.selector;

        address(this).balance;

        block.coinbase;

        msg.sender;

        tx.origin;

        S({a: 5}).a;

        type(I).creationCode;
        type(F).interfaceId;
    }
}