// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Test case for issue #1265: Library functions should not be incorrectly flagged as dead code
// when they are used via `using X for Y` syntax.

library MyLibrary {
    struct Data {
        uint256 value;
    }

    // This function IS used via `using MyLibrary for Data`
    // Should NOT be flagged as dead code (was incorrectly flagged before fix)
    function getValue(Data storage self) internal view returns (uint256) {
        return self.value;
    }

    // This function IS used via `using MyLibrary for Data`
    // Should NOT be flagged as dead code (was incorrectly flagged before fix)
    function setValue(Data storage self, uint256 newValue) internal {
        self.value = newValue;
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
