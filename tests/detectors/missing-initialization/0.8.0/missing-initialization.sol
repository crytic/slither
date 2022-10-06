contract A {
    uint public state_variable = 0;
    bool public initialized = false;

    modifier not_initialized(){
        require(initialized == false);
        _;
    }

    function initialize(uint _state_variable) public not_initialized {
        state_variable = _state_variable;
    }
}
