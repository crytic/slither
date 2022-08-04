contract C {
    function f() public {
        for (uint i = 0; i < 10; i++) {
            if (i > 100) {
                break;
            }
            if (i < 3) {
                continue;
            }

            for (uint j = 0; j < 10; j++) {
                if (j > 10) {
                    continue;
                }
                if (j < 3) {
                    break;
                }

                j -= 1;
            }
        }
    }
}
