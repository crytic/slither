contract Initializable{

    address destination;

    modifier initializer(){
        _;
    }

}

contract Contract_no_bug is Initializable{

    function initialize() public initializer{

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
