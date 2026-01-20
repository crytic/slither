// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Library with internal functions
library MyLibrary {
    struct Data {
        uint256 value;
    }

    // This function IS used via `using MyLibrary for Data`
    // Should NOT be flagged as dead code
    function getValue(Data storage self) internal view returns (uint256) {
        return self.value;
    }

    // This function IS used via `using MyLibrary for Data`
    // Should NOT be flagged as dead code
    function setValue(Data storage self, uint256 newValue) internal {
        self.value = newValue;
    }

    // This function is NOT used anywhere
    // Should be flagged as dead code
    function unusedLibraryFunction(Data storage self) internal pure returns (uint256) {
        return 42;
    }
}

contract UsingLibrary {
    using MyLibrary for MyLibrary.Data;

    MyLibrary.Data private data;

    function store(uint256 value) external {
        data.setValue(value);
    }

    function retrieve() external view returns (uint256) {
        return data.getValue();
    }
}
