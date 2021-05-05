contract C {
    function f() public {
        assembly {
            let x := 0
        }

        assembly "evmasm" {
            let x := 0
        }
    }
}