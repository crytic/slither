import {Test as TestAlias, St as StAlias, A as Aalias, Lib as LibAlias} from "./import.sol";

contract C is TestAlias{

    using LibAlias for LibAlias.Data;

    function f(StAlias storage s) internal{
        s.v = Aalias;
    }
}
