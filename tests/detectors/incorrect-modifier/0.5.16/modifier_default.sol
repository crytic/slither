contract Test {
    modifier noResult() {
        if (false) {_;}
        else if (false) {revert();}
        else {}
    }

    modifier goodRevert() {
        if (false) _;
        revert();
    }

    modifier goodCode() {
        if (false) revert();
        _;
    }

    modifier requireAssertNoResult() {
        require(1 == 1);
        assert(1 == 1);
        if (false) _;
    }

    modifier requireAssertGood() {
        require(1 == 1);
        assert(1 == 1);
        _;
    }

    modifier loopsNoResult() {
        uint8 i = 0;

        // Treated like any other conditional
        for(i = 0; i<10; i++) {_;}
        while(i < 20) {i++; _;}

        // Body is checked
        do {
            i++;
        } while (i < 30);
    }

    modifier loopGood() {
        uint8 i = 0;

        // Body is checked
        do {
            i++;
            _;
        } while (i < 1);
    }
}
