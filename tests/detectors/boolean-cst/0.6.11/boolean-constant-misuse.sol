contract MyConc {
    function bad0(bool foo) public pure returns (bool) {
        if (foo) {
            return true;
        }
        return false;
    }

    function bad1(bool b) public pure returns (bool) {
        return (b || true);
    }

    function bad2(bool x, uint8 y) public pure returns (bool) {
        while (x == (y > 0)) {
            return true;
        }
        return false;
    }

    function bad3(bool a) public pure returns (bool) {
        uint256 b = 0;
        while (a) {
            b++;
        }
        return true;
    }

    function bad4() public pure returns (bool) {
        uint256 b = 0;
        while (true) {
            b++;
        }
        return true;
    }

    function bad5() public pure returns (bool) {
        while (true) {
            return true;
        }
        return false;
    }

    function good() public pure returns (bool) {
        return true;
    }
}