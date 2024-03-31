// Vulnerable contract with potential DoS vulnerabilities
contract VulnerableContract {
    uint256[] public data;

    // Function that may lead to DoS due to inefficient gas usage
    function addData(uint256[] memory _newData) public {
        for (uint256 i = 0; i < _newData.length; i++) {
            data.push(_newData[i]);
        }
    }
}

