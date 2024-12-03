contract A {
 function a(uint256 q, uint256 e) internal virtual {}
 function b() public { a({e: 23, q: 34}); }
}

contract B is A {
 function a(uint256 w, uint256 q) internal override {}
}