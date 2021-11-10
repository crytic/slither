pragma solidity ^0.4.24;

contract Token {
    function balanceOf(address) public view returns (uint);
}


contract BalanceChecker {

    function tokenBalance(address user, address token) public view returns (uint) {
        // check if token is actually a contract
        uint256 tokenCode;
        assembly { tokenCode := extcodesize(token) } // contract code size

        // is it a contract and does it implement balanceOf
        if (tokenCode > 0 && token.call(bytes4(0x70a08231), user)) {
            return Token(token).balanceOf(user);
        } else {
            return 0;
        }
    }

    function balances(address user, address[] tokens) external view returns (uint[]) {
        uint[] memory addrBalances = new uint[](tokens.length);

        for(uint i = 0; i < tokens.length; i++) {
            addrBalances[i] = tokenBalance(user, tokens[i]);
        }
        return addrBalances;
    }
}