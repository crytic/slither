import "./Math.sol" as m;

type MyTypeA is int256;

using {m.mul, m.unwrap} for MyTypeA global;