contract C {
    // Snippet of the _checkpointPushDiff function that was making slither crashes 
    // https://github.com/Vectorized/solady/blob/9298d096feb87de9a8873a704ff98f6892064c65/src/tokens/ERC20Votes.sol#L339-L361
    function _checkpointPushDiff(uint256 lengthSlot, uint256 key, uint256 amount, bool isAdd)
        private
  returns(uint256 newValue)        
    {
        /// @solidity memory-safe-assembly
        assembly {
            let lengthSlotPacked := sload(lengthSlot)
            for { let n := shr(208, shl(160, lengthSlotPacked)) } 1 {} {
                if iszero(n) {
                    if iszero(or(isAdd, iszero(amount))) {
                        mstore(0x00, 0x5915f686) // `ERC5805CheckpointValueUnderflow()`.
                        revert(0x1c, 0x04)
                    }
                    newValue := amount
                    if iszero(or(eq(newValue, address()), shr(160, newValue))) {
                        sstore(lengthSlot, or(or(key, shl(48, 1)), shl(96, newValue)))
                        break
                    }
                    sstore(lengthSlot, or(or(key, shl(48, 1)), shl(96, address())))
                    sstore(not(lengthSlot), newValue)
                    break
                }
                let checkpointSlot := add(sub(n, 1), lengthSlot)
            }
        }
    }
}


// Snippet of the Initializable contract that was making slither crashes
// https://github.com/Vectorized/solady/blob/9298d096feb87de9a8873a704ff98f6892064c65/src/utils/Initializable.sol#L7
contract Initializable {
    bytes32 private constant _INITIALIZED_EVENT_SIGNATURE =
        0xc7f505b2f371ae2175ee4913f4499e1f2633a7b5936321eed1cdaeb6115181d2;
    bytes32 private constant _INITIALIZABLE_SLOT =
        0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffbf601132;


    function _initializableSlot() internal pure virtual returns (bytes32) {
        return _INITIALIZABLE_SLOT;
    }

    modifier initializer() virtual {
        bytes32 s = _initializableSlot();
        /// @solidity memory-safe-assembly
        assembly {
            let i := sload(s)
            // Set `initializing` to 1, `initializedVersion` to 1.
            sstore(s, 3)
            // If `!(initializing == 0 && initializedVersion == 0)`.
            if i {
                // If `!(address(this).code.length == 0 && initializedVersion == 1)`.
                if iszero(lt(extcodesize(address()), eq(shr(1, i), 1))) {
                    mstore(0x00, 0xf92ee8a9) // `InvalidInitialization()`.
                    revert(0x1c, 0x04)
                }
                s := shl(shl(255, i), s) // Skip initializing if `initializing == 1`.
            }
        }
        _;
        /// @solidity memory-safe-assembly
        assembly {
            if s {
                // Set `initializing` to 0, `initializedVersion` to 1.
                sstore(s, 2)
                // Emit the {Initialized} event.
                mstore(0x20, 1)
                log1(0x20, 0x20, _INITIALIZED_EVENT_SIGNATURE)
            }
        }
    }
}