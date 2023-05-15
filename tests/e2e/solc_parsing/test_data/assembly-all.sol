contract C {
    modifier a() {
        assembly {
            let y := 0
        }
        _;
    }

    function f() public a {
        assembly {
            let x := 0
        }

        assembly "evmasm" {
            let x := 0
        }
    }
}