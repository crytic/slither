import "./Casting.sol" as C;
import "./Math.sol" as M;

type MyTypeB is uint256;

using {M.mul, C.unwrap} for MyTypeB global;