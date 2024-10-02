import "./Casting.sol" as C;
import "./Math.sol" as M;

type MyTypeA is int256;

using {M.mul, C.unwrap} for MyTypeA global;