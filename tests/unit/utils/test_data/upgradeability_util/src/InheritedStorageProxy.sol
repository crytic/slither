pragma solidity ^0.8.0;

import "./Proxy.sol";
import "./ProxyStorage.sol";

contract InheritedStorageProxy is Proxy, ProxyStorage {
    constructor(address _implementation) {
        admin = msg.sender;
        implementation = _implementation;
    }

    function getImplementation() external view returns (address) {
        return _implementation();
    }

    function getAdmin() external view returns (address) {
        return _admin();
    }

    function upgrade(address _newImplementation) external {
        require(msg.sender == admin, "Only admin can upgrade");
        implementation = _newImplementation;
    }

    function setAdmin(address _newAdmin) external {
        require(msg.sender == admin, "Only current admin can change admin");
        admin = _newAdmin;
    }

    function _implementation() internal view override returns (address) {
        return implementation;
    }

    function _admin() internal view returns (address) {
        return admin;
    }

    function _beforeFallback() internal override {}
}
