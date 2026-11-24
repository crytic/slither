// Variables used only as array slice bounds are used (issue #2291)
contract SliceBounds {
    uint256 private constant _OPERATION_CODE_START = 0;
    uint256 private constant _OPERATION_CODE_END = 4;

    uint256 private constant _OFFSET_NUM1 = 4 + 32;
    uint256 private constant _OFFSET_NUM2 = 4 + 32 * 4;

    uint256 private _start = 1;
    uint256 private _end = 2;
    uint256 private _msgDataOffset = 4;

    // Should be reported
    uint256 private _unused = 3;

    function test(bytes calldata data) external pure {
        bytes calldata data2 = data[_OFFSET_NUM2:];

        bytes4 operationCode = 0;
        if (data.length >= _OPERATION_CODE_END) {
            operationCode = bytes4(data[_OPERATION_CODE_START:_OPERATION_CODE_END]);
        }

        data[_OFFSET_NUM1:_OFFSET_NUM2];
    }

    function sliceState(uint256[] calldata arr) external view returns (uint256[] calldata) {
        return arr[_start:_end];
    }

    function sliceMsgData() external view returns (uint256) {
        return abi.decode(msg.data[_msgDataOffset:], (uint256));
    }
}
