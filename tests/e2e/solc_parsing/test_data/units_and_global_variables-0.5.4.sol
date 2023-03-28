// this makes solc 0.5.4 crash - and actually is not needed :)
//pragma experimental ABIEncoderV2;

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
    }

    function block_and_transactions() payable public{
        blockhash(0);
        block.coinbase;
        block.difficulty;
        block.gaslimit;
        block.number;
        block.timestamp;
        gasleft();
        msg.data;
        msg.sender;
        msg.sig;
        msg.value;
        now;
        tx.gasprice;
        tx.origin;
    }

    function abi_encode() public{
        bytes memory m;
        abi.decode(m, (uint, uint));
        abi.encode(10);
        abi.encodePacked(uint(10));
        bytes4 selector;
        abi.encodeWithSelector(selector, 10);
        string memory signature;
        abi.encodeWithSignature(signature, 10);
    }

    function error_handling() public{
        assert(true);
        require(true);
        require(true, "something");
        revert();
        revert("something");
    }

    function math_and_crypto() public{
        addmod(0, 0, 1);
        mulmod(0, 0, 1);
        keccak256("");
        sha256("");
        ripemd160("");
        bytes32 hash;
        uint8 v;
        bytes32 r;
        bytes32 s;
        ecrecover(hash,v,r,s);
    }

    function address_related() public{
        address payable a;
        a.balance;
        a.send(0);
        a.transfer(0);
        a.call("");
        a.delegatecall("");
        a.staticcall("");
    }

    function contract_related() public{
        this;
        address payable a;
        selfdestruct(a);
    }
}
