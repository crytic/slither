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
    function bad(bytes memory x) public {}
    function bad2(uint256[] memory x) public {}
    function bad3(testStruct memory x) public {}
    function bad4(string memory x) public {}

}