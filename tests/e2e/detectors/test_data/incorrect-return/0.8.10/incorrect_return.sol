contract C {
    function internal_return() internal{
        assembly {
            return (5, 6)
        }
    }

    function bad0() public returns (bool){
        internal_return();
        return true;
    }

    function indirect2() internal {
        internal_return();
    }

    function indirect() internal {
        indirect2();
    }

    function bad1() public returns (bool){
        indirect();
        return true;
    }

    function good0() public{
        // Dont report if there is no following operation
        internal_return();
    }

    function good1() public returns (uint a, uint b){
        assembly {
            return (5, 6)
        }
    }
}