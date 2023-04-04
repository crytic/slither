import "./using-for-library-0.8.0.sol";

contract C {
    Data knownValues;

    function libCall(uint value) public {
        require(knownValues.a(value));
    }

    function topLevelCall(uint value) public {
        require(knownValues.d(value));
    }


}
