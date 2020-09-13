// import global
import "./helper/import-1.sol";

// import a symbol
import * as Target from "./helper/import-1.sol";

// import specific
import {D} from "./helper/import-2.sol";

// import with alias
import {A as AA, B as BB} from "./helper/import-1.sol";

contract C {
    function f() public {
        // use global
        B.X a = B.X.A;

        // use symbol
        Target.B.X b;

        // use specific
        D.Y c = D.Y.A;

        // use alias
        BB.X d = BB.X.A;
    }
}