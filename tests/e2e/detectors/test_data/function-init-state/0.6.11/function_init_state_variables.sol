// This tests the detection of initializing a state variable using a non-constant function call or state variable.

contract StateVarInitFromFunction {

    uint public v = set(); // should be flagged, initialized from function (sets to 77)
    uint public w = 5;
    uint public x = set(); // should be flagged, initialized from function (sets to 88)

    uint public y1 = 5 + get(); // should be flagged, initialized from function (in expression)
    uint public y2 = (10 + (5 + get())); // should be flagged, initialized from function (in expression)

    uint public z1 = 5 + getPure(); // should not be flagged, is a pure function
    uint public z2 = (10 + (5 + getPure())); // should not be flagged, is a pure function

    uint constant public c1 = 40;
    uint public z3 = c1 + 5; // should not be flagged, references a constant
    uint public z4 = z3 + 5; // should be flagged, uses a non-constant state variable.

    address public shouldntBeReported = address(8); // should not be flagged, not a *real* function call.
    uint public constructorV;
    uint public constructorX;

    constructor() public {
        // By the time this code is hit, all state variable initialization has completed.
        constructorV = v;
        constructorX = x;
    }

    function set() public  returns(uint)  {
        // If this function is being used to initialize a state variable before w, w will be zero.
        // If it is declared after w, w will be set.
        if(w == 0) {
            return 77;
        }

        return 88;
    }

    function get() public returns(uint) {
        return 55;
    }

    function getPure() public pure returns(uint) {
        return 55;
    }
}