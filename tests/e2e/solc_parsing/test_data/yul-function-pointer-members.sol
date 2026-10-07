contract C {
    function f() public {
        function() external g;
        assembly {
            g.selector := 1
            g.address := 2
        }
    }

    function read(function() external h) public returns (bytes4 s, address a) {
        assembly {
            s := h.selector
            a := h.address
        }
    }
}
