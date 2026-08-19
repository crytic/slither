// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Test_DeepCallChain {
    function f40(uint256 a, uint256 b) internal pure returns (uint256) { return a / b; }
    function f39(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f40(a, b); return r; }
    function f38(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f39(a, b); return r; }
    function f37(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f38(a, b); return r; }
    function f36(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f37(a, b); return r; }
    function f35(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f36(a, b); return r; }
    function f34(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f35(a, b); return r; }
    function f33(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f34(a, b); return r; }
    function f32(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f33(a, b); return r; }
    function f31(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f32(a, b); return r; }
    function f30(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f31(a, b); return r; }
    function f29(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f30(a, b); return r; }
    function f28(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f29(a, b); return r; }
    function f27(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f28(a, b); return r; }
    function f26(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f27(a, b); return r; }
    function f25(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f26(a, b); return r; }
    function f24(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f25(a, b); return r; }
    function f23(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f24(a, b); return r; }
    function f22(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f23(a, b); return r; }
    function f21(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f22(a, b); return r; }
    function f20(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f21(a, b); return r; }
    function f19(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f20(a, b); return r; }
    function f18(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f19(a, b); return r; }
    function f17(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f18(a, b); return r; }
    function f16(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f17(a, b); return r; }
    function f15(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f16(a, b); return r; }
    function f14(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f15(a, b); return r; }
    function f13(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f14(a, b); return r; }
    function f12(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f13(a, b); return r; }
    function f11(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f12(a, b); return r; }
    function f10(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f11(a, b); return r; }
    function f9(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f10(a, b); return r; }
    function f8(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f9(a, b); return r; }
    function f7(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f8(a, b); return r; }
    function f6(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f7(a, b); return r; }
    function f5(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f6(a, b); return r; }
    function f4(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f5(a, b); return r; }
    function f3(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f4(a, b); return r; }
    function f2(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f3(a, b); return r; }
    function f1(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f2(a, b); return r; }
    function f0(uint256 a, uint256 b) internal pure returns (uint256) { uint256 r = f1(a, b); return r; }
    function entry(uint256 x, uint256 y) external pure returns (uint256) { uint256 result = f0(x, y); return result; }
}
