pragma experimental ABIEncoderV2;
contract I {

}

interface F {
    
}

contract C {
    struct S {
        uint a;
    }

    struct A {
        uint balance;
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
        type(int).min;
        type(int).max;
    }

    function g(A memory self) public {
        self.balance = 1;
    }

}