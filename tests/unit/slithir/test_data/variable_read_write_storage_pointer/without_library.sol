// Simplified from https://github.com/crytic/slither/issues/2598 

pragma solidity ^0.8.0;

contract MinterRole {

    struct Role {
        mapping (address => bool) bearer;
    }


    /**
     * @dev Give an account access to this role.
     */
    function add(Role storage role, address account) internal {
        require(!has(role, account), "Roles: account already has role");
        role.bearer[account] = true;
    }

    function has(Role storage role, address account) internal view returns (bool) {
        require(account != address(0), "Roles: account is the zero address");
        return role.bearer[account];
    }

    Role private _minters;

    function addMinter(address account) public {
        _addMinter(account);
    }

    function _addMinter(address account) internal {
        add(_minters, account);
    }

}   