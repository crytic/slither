type Operand is uint256;
type StackTop is uint256;
struct StorageOpcodesRange {
    uint256 pointer;
    uint256 length;
}
struct IntegrityState {
    // Sources first as we read it in assembly.
    bytes[] sources;
    StorageOpcodesRange storageOpcodesRange;
    uint256 constantsLength;
    uint256 contextLength;
    StackTop stackBottom;
    StackTop stackMaxTop;
    uint256 contextScratch;
    function(IntegrityState memory, Operand, StackTop)
        view
        returns (StackTop)[] integrityFunctionPointers;
}

contract Test {
    function set(StackTop stackTop_, uint256 a_) internal pure {
        assembly {
            mstore(stackTop_, a_)
        }
    }
}