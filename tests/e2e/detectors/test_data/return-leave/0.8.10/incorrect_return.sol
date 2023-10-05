contract C {

    function f() internal returns (uint a, uint b){
        assembly {
            return (5, 6)
        }
    }
}