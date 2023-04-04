contract Test{

    function ether_unit() public{
        1 wei;
        1 finney;
        1 szabo;
        1 ether;
    }

    function time_unit() public{
        1 seconds;
        1 minutes;
        1 hours;
        1 days;
        1 weeks;
        1 years;
    }

    function block_and_transactions() public{
        block.blockhash(0);
        block.coinbase;
        block.difficulty;
        block.gaslimit;
        block.number;
        block.timestamp;
        msg.data;
        msg.gas;
        msg.sender;
        msg.sig;
        msg.value;
        now;
        tx.gasprice;
        tx.origin;
    }


    function math_and_crypto() public{
        addmod(0, 0, 1);
        mulmod(0, 0, 1);
        sha3("");
        sha256("");
        ripemd160("");
        bytes32 hash;
        uint8 v;
        bytes32 r;
        bytes32 s;
        ecrecover(hash,v,r,s);
    }

    function address_related() public{
        address a;
        a.balance;
        a.send(0);
    }

    function contract_related() public{
        this;
        address a;
        selfdestruct(a);
    }
}
