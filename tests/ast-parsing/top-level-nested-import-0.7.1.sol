import "./helper/nested_import.sol";

contract C{


    function f() public{
        Helper._require(true, 1);
    }
}

