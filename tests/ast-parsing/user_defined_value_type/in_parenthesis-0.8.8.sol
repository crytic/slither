type MyInt is int;
contract C {
    function f() public returns (MyInt a, int b) {
        (MyInt).wrap;
        a = (MyInt).wrap(5);
        (MyInt).unwrap;
        b = (MyInt).unwrap((MyInt).wrap(10));
    }
}

// Represent a 18 decimal, 256 bit wide fixed point type
// using a user defined value type.
type UFixed is uint256;

/// A minimal library to do fixed point operations on UFixed.
library FixedMath {
    uint constant multiplier = 10**18;

    /// Adds two UFixed numbers. Reverts on overflow, 
    /// relying on checked arithmetic on uint256.
    function add(UFixed a, UFixed b) internal pure returns (UFixed) {
        return UFixed.wrap(UFixed.unwrap(a) + UFixed.unwrap(b));
    }
    /// Multiplies UFixed and uint256. Reverts on overflow,
    /// relying on checked arithmetic on uint256.
    function mul(UFixed a, uint256 b) internal pure returns (UFixed) {
        return UFixed.wrap(UFixed.unwrap(a) * b);
    }
    /// Take the floor of a UFixed number.
    /// @return the largest integer that does not exceed `a`.
    function floor(UFixed a) internal pure returns (uint256) {
        return UFixed.unwrap(a) / multiplier;
    }
    /// Turns a uint256 into a UFixed of the same value.
    /// Reverts if the integer is too large.
    function toUFixed(uint256 a) internal pure returns (UFixed) {
        return UFixed.wrap(a * multiplier);
    }
}


contract Greeter {
    using FixedMath for UFixed;
    UFixed public someValue;

    constructor(string memory _greeting) {
    }
}
