/// @dev returns the smaller of the two values.
function min(uint x, uint y) pure returns (uint) {
    return x < y ? x : y;
}

/// @dev returns the sum of the elements of the storage array
function sum(uint[] storage items) view returns (uint s) {
    for (uint i = 0; i < items.length; i++)
        s += items[i];
}

