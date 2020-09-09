import "./double.sol";


contract IfExample {
    Double d = new Double();

    function if_statement(uint256 x) public returns (uint256) {
        uint256 ret = 0;
        do_nothing(x);
        if (x == 2) {
            ret = d.double(x);
        }
        return ret;
    }

    function do_nothing(uint256 x) public returns (uint256) {
        return x;
    }
}
