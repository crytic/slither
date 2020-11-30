contract MyConc {
    function bad0() public pure returns (bool) {
        if (false) {
            return true;
        }
    }

    function bad1(bool b) public pure returns (bool) {
        return (b || true);
    }

    function bad2(bool x, uint8 y) public pure returns (bool) {
        if (x == (y > 0)) {
            return true;
        }
    }

    function bad3() public pure returns (bool) {
        uint256 a;
        if (a == 10) {
            return true;
        }
    }
    function good(uint8 a) public pure returns (bool) { 
        return a >= 1;
    }
}
