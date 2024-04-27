pragma solidity 0.8.24;

library Lib {
 function a(uint q) public {}
}
function c(uint z)  {}

using {Lib.a} for uint;
using {c} for uint;

function b(uint y)  {
 Lib.a(4);
 y.c();
 y.a();
}