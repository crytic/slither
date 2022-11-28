contract TestReentrant{

    modifier nonReentrant(){
        _;
    }

    function check_is_reentrant() public{
        internal_func_reentrant();
    }

    function check_is_non_reentrant() nonReentrant() public{
        internal_func_not_reentrant();
    }

    function internal_func_not_reentrant() internal{

    }

    function internal_func_reentrant() internal{

    }

}