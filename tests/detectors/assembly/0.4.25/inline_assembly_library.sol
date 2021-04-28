pragma solidity ^0.4.16;

// taken from https://solidity.readthedocs.io/en/v0.4.25/assembly.html

library VectorSum {
    // This function is less efficient because the optimizer currently fails to
    // remove the bounds checks in array access.
    function sumSolidity(uint[] _data) public view returns (uint o_sum) {
        for (uint i = 0; i < _data.length; ++i)
            o_sum += _data[i];
    }

    // We know that we only access the array in bounds, so we can avoid the check.
    // 0x20 needs to be added to an array because the first slot contains the
    // array length.
    function sumAsm(uint[] _data) public view returns (uint o_sum) {
        for (uint i = 0; i < _data.length; ++i) {
            assembly {
                o_sum := add(o_sum, mload(add(add(_data, 0x20), mul(i, 0x20))))
            }
        }
    }

    // Same as above, but accomplish the entire code within inline assembly.
    function sumPureAsm(uint[] _data) public view returns (uint o_sum) {
        assembly {
           // Load the length (first 32 bytes)
           let len := mload(_data)

           // Skip over the length field.
           //
           // Keep temporary variable so it can be incremented in place.
           //
           // NOTE: incrementing _data would result in an unusable
           //       _data variable after this assembly block
           let data := add(_data, 0x20)

           // Iterate until the bound is not met.
           for
               { let end := add(data, len) }
               lt(data, end)
               { data := add(data, 0x20) }
           {
               o_sum := add(o_sum, mload(data))
           }
        }
    }
}

