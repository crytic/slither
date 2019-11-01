pragma solidity >=0.4.24;

contract Vat {
  mapping (address => uint256)                   public dai;  // [rad]
  mapping (address => uint256)                   public sin;  // [rad]
  uint256 public debt;  // Total Dai Issued    [rad]
  uint256 public vice;  // Total Unbacked Dai  [rad]
  
  function sub(uint x, int y) internal pure returns (uint z) {
        z = x - uint(y);
        require(y <= 0 || z <= x);
        require(y >= 0 || z >= x);
  }
  
  function heal(int rad) public {
    sin[msg.sender] = sub(sin[msg.sender], rad);
    dai[msg.sender] = sub(dai[msg.sender], rad);
    vice   = sub(vice,   rad);
    debt   = sub(debt,   rad);
  }
}
