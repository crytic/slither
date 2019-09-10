pragma solidity ^0.4.10;

contract GasToken2 {
    //////////////////////////////////////////////////////////////////////////
    // RLP.sol
    // Due to some unexplained bug, we get a slightly different bytecode if 
    // we use an import, and are then unable to verify the code in Etherscan
    //////////////////////////////////////////////////////////////////////////
    
    uint256 constant ADDRESS_BYTES = 20;
    uint256 constant MAX_SINGLE_BYTE = 128;
    uint256 constant MAX_NONCE = 256**9 - 1;

    // count number of bytes required to represent an unsigned integer
    function count_bytes(uint256 n) constant internal returns (uint256 c) {
        uint i = 0;
        uint mask = 1;
        while (n >= mask) {
            i += 1;
            mask *= 256;
        }

        return i;
    }

    function mk_contract_address(address a, uint256 n) constant internal returns (address rlp) {
        /*
         * make sure the RLP encoding fits in one word:
         * total_length      1 byte
         * address_length    1 byte
         * address          20 bytes
         * nonce_length      1 byte (or 0)
         * nonce           1-9 bytes
         *                ==========
         *                24-32 bytes
         */
        require(n <= MAX_NONCE);

        // number of bytes required to write down the nonce
        uint256 nonce_bytes;
        // length in bytes of the RLP encoding of the nonce
        uint256 nonce_rlp_len;

        if (0 < n && n < MAX_SINGLE_BYTE) {
            // nonce fits in a single byte
            // RLP(nonce) = nonce
            nonce_bytes = 1;
            nonce_rlp_len = 1;
        } else {
            // RLP(nonce) = [num_bytes_in_nonce nonce]
            nonce_bytes = count_bytes(n);
            nonce_rlp_len = nonce_bytes + 1;
        }

        // [address_length(1) address(20) nonce_length(0 or 1) nonce(1-9)]
        uint256 tot_bytes = 1 + ADDRESS_BYTES + nonce_rlp_len;

        // concatenate all parts of the RLP encoding in the leading bytes of
        // one 32-byte word
        uint256 word = ((192 + tot_bytes) * 256**31) +
                       ((128 + ADDRESS_BYTES) * 256**30) +
                       (uint256(a) * 256**10);

        if (0 < n && n < MAX_SINGLE_BYTE) {
            word += n * 256**9;
        } else {
            word += (128 + nonce_bytes) * 256**9;
            word += n * 256**(9 - nonce_bytes);
        }

        uint256 hash;

        assembly {
            let mem_start := mload(0x40)        // get a pointer to free memory
            mstore(0x40, add(mem_start, 0x20))  // update the pointer

            mstore(mem_start, word)             // store the rlp encoding
            hash := sha3(mem_start,
                         add(tot_bytes, 1))     // hash the rlp encoding
        }

        // interpret hash as address (20 least significant bytes)
        return address(hash);
    }
    
    //////////////////////////////////////////////////////////////////////////
    // Generic ERC20
    //////////////////////////////////////////////////////////////////////////

    // owner -> amount
    mapping(address => uint256) s_balances;
    // owner -> spender -> max amount
    mapping(address => mapping(address => uint256)) s_allowances;

    event Transfer(address indexed from, address indexed to, uint256 value);

    event Approval(address indexed owner, address indexed spender, uint256 value);

    // Spec: Get the account balance of another account with address `owner`
    function balanceOf(address owner) public constant returns (uint256 balance) {
        return s_balances[owner];
    }

    function internalTransfer(address from, address to, uint256 value) internal returns (bool success) {
        if (value <= s_balances[from]) {
            s_balances[from] -= value;
            s_balances[to] += value;
            Transfer(from, to, value);
            return true;
        } else {
            return false;
        }
    }

    // Spec: Send `value` amount of tokens to address `to`
    function transfer(address to, uint256 value) public returns (bool success) {
        address from = msg.sender;
        return internalTransfer(from, to, value);
    }

    // Spec: Send `value` amount of tokens from address `from` to address `to`
    function transferFrom(address from, address to, uint256 value) public returns (bool success) {
        address spender = msg.sender;
        if(value <= s_allowances[from][spender] && internalTransfer(from, to, value)) {
            s_allowances[from][spender] -= value;
            return true;
        } else {
            return false;
        }
    }

    // Spec: Allow `spender` to withdraw from your account, multiple times, up
    // to the `value` amount. If this function is called again it overwrites the
    // current allowance with `value`.
    function approve(address spender, uint256 value) public returns (bool success) {
        address owner = msg.sender;
        if (value != 0 && s_allowances[owner][spender] != 0) {
            return false;
        }
        s_allowances[owner][spender] = value;
        Approval(owner, spender, value);
        return true;
    }

    // Spec: Returns the `amount` which `spender` is still allowed to withdraw
    // from `owner`.
    // What if the allowance is higher than the balance of the `owner`?
    // Callers should be careful to use min(allowance, balanceOf) to make sure
    // that the allowance is actually present in the account!
    function allowance(address owner, address spender) public constant returns (uint256 remaining) {
        return s_allowances[owner][spender];
    }

    //////////////////////////////////////////////////////////////////////////
    // GasToken specifics
    //////////////////////////////////////////////////////////////////////////

    uint8 constant public decimals = 2;
    string constant public name = "Gastoken.io";
    string constant public symbol = "GST2";

    // We build a queue of nonces at which child contracts are stored. s_head is
    // the nonce at the head of the queue, s_tail is the nonce behind the tail
    // of the queue. The queue grows at the head and shrinks from the tail.
    // Note that when and only when a contract CREATEs another contract, the
    // creating contract's nonce is incremented.
    // The first child contract is created with nonce == 1, the second child
    // contract is created with nonce == 2, and so on...
    // For example, if there are child contracts at nonces [2,3,4],
    // then s_head == 4 and s_tail == 1. If there are no child contracts,
    // s_head == s_tail.
    uint256 s_head;
    uint256 s_tail;

    // totalSupply gives  the number of tokens currently in existence
    // Each token corresponds to one child contract that can be SELFDESTRUCTed
    // for a gas refund.
    function totalSupply() public constant returns (uint256 supply) {
        return s_head - s_tail;
    }

    // Creates a child contract that can only be destroyed by this contract.
    function makeChild() internal returns (address addr) {
        assembly {
            // EVM assembler of runtime portion of child contract:
            //     ;; Pseudocode: if (msg.sender != 0x0000000000b3f879cb30fe243b4dfee438691c04) { throw; }
            //     ;;             suicide(msg.sender)
            //     PUSH15 0xb3f879cb30fe243b4dfee438691c04 ;; hardcoded address of this contract
            //     CALLER
            //     XOR
            //     PC
            //     JUMPI
            //     CALLER
            //     SELFDESTRUCT
            // Or in binary: 6eb3f879cb30fe243b4dfee438691c043318585733ff
            // Since the binary is so short (22 bytes), we can get away
            // with a very simple initcode:
            //     PUSH22 0x6eb3f879cb30fe243b4dfee438691c043318585733ff
            //     PUSH1 0
            //     MSTORE ;; at this point, memory locations mem[10] through
            //            ;; mem[31] contain the runtime portion of the child
            //            ;; contract. all that's left to do is to RETURN this
            //            ;; chunk of memory.
            //     PUSH1 22 ;; length
            //     PUSH1 10 ;; offset
            //     RETURN
            // Or in binary: 756eb3f879cb30fe243b4dfee438691c043318585733ff6000526016600af3
            // Almost done! All we have to do is put this short (31 bytes) blob into
            // memory and call CREATE with the appropriate offsets.
            let solidity_free_mem_ptr := mload(0x40)
            mstore(solidity_free_mem_ptr, 0x00756eb3f879cb30fe243b4dfee438691c043318585733ff6000526016600af3)
            addr := create(0, add(solidity_free_mem_ptr, 1), 31)
        }
    }

    // Mints `value` new sub-tokens (e.g. cents, pennies, ...) by creating `value`
    // new child contracts. The minted tokens are owned by the caller of this
    // function.
    function mint(uint256 value) public {
        for (uint256 i = 0; i < value; i++) {
            makeChild();
        }
        s_head += value;
        s_balances[msg.sender] += value;
    }

    // Destroys `value` child contracts and updates s_tail.
    //
    // This function is affected by an issue in solc: https://github.com/ethereum/solidity/issues/2999
    // The `mk_contract_address(this, i).call();` doesn't forward all available gas, but only GAS - 25710.
    // As a result, when this line is executed with e.g. 30000 gas, the callee will have less than 5000 gas
    // available and its SELFDESTRUCT operation will fail leading to no gas refund occurring.
    // The remaining ~29000 gas left after the call is enough to update s_tail and the caller's balance.
    // Hence tokens will have been destroyed without a commensurate gas refund.
    // Fortunately, there is a simple workaround:
    // Whenever you call free, freeUpTo, freeFrom, or freeUpToFrom, ensure that you pass at least
    // 25710 + `value` * (1148 + 5722 + 150) gas. (It won't all be used)
    function destroyChildren(uint256 value) internal {
        uint256 tail = s_tail;
        // tail points to slot behind the last contract in the queue
        for (uint256 i = tail + 1; i <= tail + value; i++) {
            mk_contract_address(this, i).call();
        }

        s_tail = tail + value;
    }

    // Frees `value` sub-tokens (e.g. cents, pennies, ...) belonging to the
    // caller of this function by destroying `value` child contracts, which
    // will trigger a partial gas refund.
    // You should ensure that you pass at least 25710 + `value` * (1148 + 5722 + 150) gas
    // when calling this function. For details, see the comment above `destroyChilden`.
    function free(uint256 value) public returns (bool success) {
        uint256 from_balance = s_balances[msg.sender];
        if (value > from_balance) {
            return false;
        }

        destroyChildren(value);

        s_balances[msg.sender] = from_balance - value;

        return true;
    }

    // Frees up to `value` sub-tokens. Returns how many tokens were freed.
    // Otherwise, identical to free.
    // You should ensure that you pass at least 25710 + `value` * (1148 + 5722 + 150) gas
    // when calling this function. For details, see the comment above `destroyChilden`.
    function freeUpTo(uint256 value) public returns (uint256 freed) {
        uint256 from_balance = s_balances[msg.sender];
        if (value > from_balance) {
            value = from_balance;
        }

        destroyChildren(value);

        s_balances[msg.sender] = from_balance - value;

        return value;
    }

    // Frees `value` sub-tokens owned by address `from`. Requires that `msg.sender`
    // has been approved by `from`.
    // You should ensure that you pass at least 25710 + `value` * (1148 + 5722 + 150) gas
    // when calling this function. For details, see the comment above `destroyChilden`.
    function freeFrom(address from, uint256 value) public returns (bool success) {
        address spender = msg.sender;
        uint256 from_balance = s_balances[from];
        if (value > from_balance) {
            return false;
        }

        mapping(address => uint256) from_allowances = s_allowances[from];
        uint256 spender_allowance = from_allowances[spender];
        if (value > spender_allowance) {
            return false;
        }

        destroyChildren(value);

        s_balances[from] = from_balance - value;
        from_allowances[spender] = spender_allowance - value;

        return true;
    }

    // Frees up to `value` sub-tokens owned by address `from`. Returns how many tokens were freed.
    // Otherwise, identical to `freeFrom`.
    // You should ensure that you pass at least 25710 + `value` * (1148 + 5722 + 150) gas
    // when calling this function. For details, see the comment above `destroyChilden`.
    function freeFromUpTo(address from, uint256 value) public returns (uint256 freed) {
        address spender = msg.sender;
        uint256 from_balance = s_balances[from];
        if (value > from_balance) {
            value = from_balance;
        }

        mapping(address => uint256) from_allowances = s_allowances[from];
        uint256 spender_allowance = from_allowances[spender];
        if (value > spender_allowance) {
            value = spender_allowance;
        }

        destroyChildren(value);

        s_balances[from] = from_balance - value;
        from_allowances[spender] = spender_allowance - value;

        return value;
    }
}