contract C {
    function normalLoopBlockBody() public {
        uint c;
        for (uint i = 0; i < 10; i++) {
            c++;
        }
    }
    function normalLoopExprBody() public {
        uint c;
        for (uint i = 0; i < 10; i++) c++;
    }
    function normalLoopNoBody() public {
        uint c;
        for (uint i = 0; i < 10; i++) {
        }
    }
    function loopNoPre() public {
        uint c;

        uint i = 0;
        for (; i < 10; i++) {
            c++;
        }
    }
    function loopNoCond() public {
        uint c;
        for (uint i = 0; ; i++) {
            if (i >= 10) break;
            c++;
        }
    }
    function loopNoPost() public {
        uint c;
        for (uint i = 0; i < 10; ) {
            c++;
            i++;
        }
    }
    function loopNoPreCond() public {
        uint c;

        uint i = 0;
        for (; ; i++) {
            if (i >= 10) break;
            c++;
        }
    }
    function loopNoPrePost() public {
        uint c;
        uint i = 0;
        for (; i < 10; ) {
            c++;
            i++;
        }
    }
    function loopNoCondPost() public {
        uint c;
        for (uint i = 0; ;) {
            if (i >= 10) break;
            c++;
            i++;
        }
    }
    function loopNoPreCondPost() public {
        uint c;
        uint i = 0;
        for (; ;) {
            if (i >= 10) break;
            c++;
            i++;
        }
    }
    function loopNoPreCondPostBody() public {
        for (;;) {}
    }
}