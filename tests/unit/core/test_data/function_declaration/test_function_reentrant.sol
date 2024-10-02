contract TestReentrant{

    modifier nonReentrant(){
        _;
    }

    function is_reentrant() public{
        internal_and_could_be_reentrant();
        internal_and_reentrant();
    }

    function is_non_reentrant() nonReentrant() public{
        internal_and_could_be_reentrant();
        internal_and_not_reentrant2();
    }

    function internal_and_not_reentrant() nonReentrant() internal{

    }

    function internal_and_not_reentrant2() internal{

    }

    // Called by a protected and unprotected function
    function internal_and_could_be_reentrant() internal{

    }

    // Called by a protected and unprotected function
    function internal_and_reentrant() internal{

    }


}