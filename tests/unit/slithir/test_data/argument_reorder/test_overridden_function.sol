contract A {
 function a(uint256 e, uint256 q, uint256 w) internal virtual {}
 function b() public { a({e: 23, w: 34, q: 36}); }
}

contract B is A {
 function a(uint256 q, uint256 ww, uint256 e) internal override {}
}