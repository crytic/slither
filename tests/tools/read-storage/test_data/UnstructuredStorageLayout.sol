pragma solidity 0.8.10;
// overwrite abi and bin:
// solc UnstructuredStorageLayout.sol --abi --bin --overwrite

library StorageSlot {
    struct AddressSlot {
        address value;
    }

    struct BooleanSlot {
        bool value;
    }

    struct Bytes32Slot {
        bytes32 value;
    }

    struct Uint256Slot {
        uint256 value;
    }

    /**
     * @dev Returns an `AddressSlot` with member `value` located at `slot`.
     */
    function getAddressSlot(bytes32 slot) internal pure returns (AddressSlot storage r) {
        /// @solidity memory-safe-assembly
        assembly {
            r.slot := slot
        }
    }

    /**
     * @dev Returns an `BooleanSlot` with member `value` located at `slot`.
     */
    function getBooleanSlot(bytes32 slot) internal pure returns (BooleanSlot storage r) {
        /// @solidity memory-safe-assembly
        assembly {
            r.slot := slot
        }
    }

    /**
     * @dev Returns an `Bytes32Slot` with member `value` located at `slot`.
     */
    function getBytes32Slot(bytes32 slot) internal pure returns (Bytes32Slot storage r) {
        /// @solidity memory-safe-assembly
        assembly {
            r.slot := slot
        }
    }

    /**
     * @dev Returns an `Uint256Slot` with member `value` located at `slot`.
     */
    function getUint256Slot(bytes32 slot) internal pure returns (Uint256Slot storage r) {
        /// @solidity memory-safe-assembly
        assembly {
            r.slot := slot
        }
    }
}

contract UnstructuredStorageLayout {

    bytes32 constant ADMIN_SLOT = keccak256("org.zeppelinos.proxy.admin");
    // This is the keccak-256 hash of "eip1967.proxy.implementation" subtracted by 1.
    bytes32 internal constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    // This is the keccak-256 hash of "eip1967.proxy.rollback" subtracted by 1
    bytes32 private constant ROLLBACK_SLOT = 0x4910fdfa16fed3260ed0e7147f7cc6da11a60208b5b9406d12a635614ffd9143;
    bytes32 constant BEACON_SLOT = bytes32(uint256(keccak256('eip1967.proxy.beacon')) - 1);

    address internal masterCopy;

    function _admin() internal view returns (address admin) {
        bytes32 slot = ADMIN_SLOT;
        assembly {
            admin := sload(slot)
        }
    }

    function _implementation() internal view returns (address) {
        address _impl;
        bytes32 slot = IMPLEMENTATION_SLOT;
        assembly {
            _impl := sload(slot)
        }
        return _impl;
    }

    function _set_rollback(bool _rollback) internal {
        StorageSlot.getBooleanSlot(ROLLBACK_SLOT).value = _rollback;
    }

    function _set_beacon(address _beacon) internal {
        bytes32 slot = bytes32(uint256(keccak256('eip1967.proxy.beacon')) - 1);
        assembly {
            sstore(slot, _beacon)
        }
    }

    function store() external {
        address admin = _admin();
        require(admin == address(0));

        bytes32 admin_slot = ADMIN_SLOT;
        address sender = msg.sender;
        assembly {
            sstore(admin_slot, sender)
        }

        bytes32 impl_slot = IMPLEMENTATION_SLOT;
        address _impl = address(0x0054006763154c764da4af42a8c3cfc25ea29765d5);
        assembly {
            sstore(impl_slot, _impl)
            sstore(0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7, _impl)
        }

        _set_rollback(true);
        _set_beacon(address(0x0054006763154c764da4af42a8c3cfc25ea29765d5));
    }

    // Code position in storage is keccak256("PROXIABLE") = "0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7"
    fallback() external {
        assembly { // solium-disable-line
            let nonsense := sload(sub(1,1))
            let _masterCopy := and(sload(0), 0xffffffffffffffffffffffffffffffffffffffff)
            let contractLogic := sload(0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7)
            calldatacopy(0x0, 0x0, calldatasize())
            let success := delegatecall(gas(), contractLogic, 0x0, calldatasize(), 0, 0)
            let retSz := returndatasize()
            returndatacopy(0, 0, retSz)
            switch success
            case 0 {
                revert(0, retSz)
            }
            default {
                return(0, retSz)
            }
        }
    }
}
