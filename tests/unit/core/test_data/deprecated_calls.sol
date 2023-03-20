contract ContractWithDeprecatedReferences {
    bytes32 globalBlockHash = block.blockhash(0);

    // Deprecated: Change constant -> view
    function functionWithDeprecatedThrow() public constant {
        // Deprecated: Change msg.gas -> gasleft()
        if(msg.gas == msg.value) {
            // Deprecated: Change throw -> revert()
            throw;
        }
    }

    // Deprecated: Change constant -> view
    function functionWithDeprecatedReferences() public constant {
        // Deprecated: Change sha3() -> keccak256()
        bytes32 sha3Result = sha3("test deprecated sha3 usage");

        // Deprecated: Change block.blockhash() -> blockhash()
        bytes32 blockHashResult = block.blockhash(0);

        // Deprecated: Change callcode() -> delegatecall()
        address(this).callcode();

        // Deprecated: Change suicide() -> selfdestruct()
        suicide(address(0));
    }
}