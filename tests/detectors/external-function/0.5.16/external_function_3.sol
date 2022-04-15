pragma experimental ABIEncoderV2;

contract Test {

    struct testStruct {
        uint256 id;
        string name;
    }

    function good(bytes calldata x) external {}
    function good2() public {}
    function good3(uint256 x, uint256 y) public {}
    function good4(uint256[] calldata x, string calldata y) external {}
    function good5(testStruct calldata x) external {}

}