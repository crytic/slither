contract Parser {
    string example = "1234.0";
    // parseInt(parseFloat*10^_b)
    function parseInt(string memory _a, uint _b) public pure returns (int) {
        bytes memory bresult = bytes(_a);
        int mint = 0;
        uint extra = uint(-1);
        bool decimals = false;
        bool negative = false;
        for (uint i=0; i<bresult.length; i++){
            if ((i == 0) && (bresult[i] == '-')) {
                negative = true;
            }
            extra = extra + uint(-1);
            if ((uint8(bresult[i]) >= 48) && (uint8(bresult[i]) <= 57)) {
                if (decimals){
                   if (_b == 0) break;
                    else _b--;
                    //assert(false);
                }
                mint *= 10;
                mint += uint8(bresult[i]) - 48;
            } else if (uint8(bresult[i]) == 46) decimals = true;
        }
        if (_b > 0) mint *= int(10**_b);
        if (negative) { mint *= -1;  }
        return mint;
    }
}