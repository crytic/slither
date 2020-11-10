contract C {
    function f() public {
        uint c;

        for (uint i = 0; i < 10; i++) {
            if (i % 2 == 0) {
                break;
            }
            c++;
        }

        for (uint j = 0; j < 10; j++) {
            for (uint k = 0; k < 10; k++) {
                if (j % 2 == 0 && k % 3 == 0) {
                    break;
                }
                c++;
            }
        }
    }
}