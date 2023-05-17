contract T {
    function a(int256[] memory data) public returns(int256) {
        return -data[0];
    }
}