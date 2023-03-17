
contract Placeholder {
    constructor() payable {}
}

contract NewContract {
    bytes32 internal constant state_variable_read = bytes32(0);

    function readAllStateVariables() external {
        new Placeholder{salt: state_variable_read} ();
    }

    function readAllLocalVariables() external {
        bytes32 local_variable_read = bytes32(0);
        new Placeholder{salt: local_variable_read} ();
    }
}