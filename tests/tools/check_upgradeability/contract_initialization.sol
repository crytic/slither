contract Initializable{

    address destination;

    modifier initializer(){
        _;
    }

    modifier reinitializer(uint64 version){
        _;
    }

}

contract Contract_no_bug is Initializable{

    function initialize() public initializer{

    }

}

contract Contract_no_bug_reinitializer is Initializable{

    function initialize() public reinitializer(2){

    }

}

contract Contract_lack_to_call_modifier is Initializable{

    function initialize() public {

    }
}

contract Contract_not_called_super_init is Contract_no_bug{

    function initialize() public initializer{

    }

}

contract Contract_no_bug_inherits is Contract_no_bug{

    function initialize() public initializer{
        Contract_no_bug.initialize();
    }

}

contract Contract_double_call is Contract_no_bug, Contract_no_bug_inherits{

    function initialize() public initializer{
        Contract_no_bug_inherits.initialize();
        Contract_no_bug.initialize();
    }

}

contract Contract_reinitializer_V2 is Initializable {
    uint256 public x;

    function initialize(uint256 _x) public initializer {
        x = _x;
    }

    function initializeV2(uint256 _x) public reinitializer(2) {
        x = _x;
    }

    function changeX() public {
        x++;
    }
}

contract Counter_reinitializer_V3_V4 is Initializable {
    uint256 public x;
    uint256 public y;
    uint256 public z;

    function initialize(uint256 _x) public initializer {
        x = _x;
    }

    function initializeV2(uint256 _x) public reinitializer(2) {
        x = _x;
    }

    function initializeV3(uint256 _y) public reinitializer(3) {
        y = _y;
    }

    function initializeV4(uint256 _z) public reinitializer(4) {
        z = _z;
    }

    function changeX() public {
        x = x + y + z;
    }
}