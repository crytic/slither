contract Test {

    function good(bytes x) external {}
    function good2() public {}
    function good3(uint256 x, uint256 y) public {}
    function good4(uint256[] x, string y) external {}
    function bad(bytes memory x) public {}
    function bad2(uint256[] memory x) public {}
    function bad3(string memory x) public {}

}