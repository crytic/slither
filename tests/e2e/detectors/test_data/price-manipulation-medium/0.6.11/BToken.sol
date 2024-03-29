// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.6.0;

import "./BNum.sol";


/************************************************************************************************
Originally from https://github.com/balancer-labs/balancer-core/blob/master/contracts/BToken.sol

This source code has been modified from the original, which was copied from the github repository
at commit hash f4ed5d65362a8d6cec21662fb6eae233b0babc1f.

Subject to the GPL-3.0 license
*************************************************************************************************/


// Highly opinionated token implementation
interface IERC20 {
  event Approval(address indexed src, address indexed dst, uint256 amt);
  event Transfer(address indexed src, address indexed dst, uint256 amt);

  function name() external view returns (string memory);

  function symbol() external view returns (string memory);

  function decimals() external view returns (uint8);

  function totalSupply() external view returns (uint256);

  function balanceOf(address whom) external view returns (uint256);

  function allowance(address src, address dst) external view returns (uint256);

  function approve(address dst, uint256 amt) external returns (bool);

  function transfer(address dst, uint256 amt) external returns (bool);

  function transferFrom(
    address src,
    address dst,
    uint256 amt
  ) external returns (bool);
}


contract BTokenBase is BNum {
  mapping(address => uint256) internal _balance;
  mapping(address => mapping(address => uint256)) internal _allowance;
  uint256 internal _totalSupply;

  event Approval(address indexed src, address indexed dst, uint256 amt);
  event Transfer(address indexed src, address indexed dst, uint256 amt);

  function _mint(uint256 amt) internal {
    _balance[address(this)] = badd(_balance[address(this)], amt);
    _totalSupply = badd(_totalSupply, amt);
    emit Transfer(address(0), address(this), amt);
  }

  function _burn(uint256 amt) internal {
    require(_balance[address(this)] >= amt, "ERR_INSUFFICIENT_BAL");
    _balance[address(this)] = bsub(_balance[address(this)], amt);
    _totalSupply = bsub(_totalSupply, amt);
    emit Transfer(address(this), address(0), amt);
  }

  function _move(
    address src,
    address dst,
    uint256 amt
  ) internal {
    require(_balance[src] >= amt, "ERR_INSUFFICIENT_BAL");
    _balance[src] = bsub(_balance[src], amt);
    _balance[dst] = badd(_balance[dst], amt);
    emit Transfer(src, dst, amt);
  }

  function _push(address to, uint256 amt) internal {
    _move(address(this), to, amt);
  }

  function _pull(address from, uint256 amt) internal {
    _move(from, address(this), amt);
  }
}


contract BToken is BTokenBase, IERC20 {
  uint8 private constant DECIMALS = 18;
  string private _name;
  string private _symbol;

  function _initializeToken(string memory name, string memory symbol) internal {
    require(
      bytes(_name).length == 0 &&
      bytes(name).length != 0 &&
      bytes(symbol).length != 0,
      "ERR_BTOKEN_INITIALIZED"
    );
    _name = name;
    _symbol = symbol;
  }

  function name()
    external
    override
    view
    returns (string memory)
  {
    return _name;
  }

  function symbol()
    external
    override
    view
    returns (string memory)
  {
    return _symbol;
  }

  function decimals()
    external
    override
    view
    returns (uint8)
  {
    return DECIMALS;
  }

  function allowance(address src, address dst)
    external
    override
    view
    returns (uint256)
  {
    return _allowance[src][dst];
  }

  function balanceOf(address whom) external override view returns (uint256) {
    return _balance[whom];
  }

  function totalSupply() public override view returns (uint256) {
    return _totalSupply;
  }

  function approve(address dst, uint256 amt) external override returns (bool) {
    _allowance[msg.sender][dst] = amt;
    emit Approval(msg.sender, dst, amt);
    return true;
  }

  function increaseApproval(address dst, uint256 amt) external returns (bool) {
    _allowance[msg.sender][dst] = badd(_allowance[msg.sender][dst], amt);
    emit Approval(msg.sender, dst, _allowance[msg.sender][dst]);
    return true;
  }

  function decreaseApproval(address dst, uint256 amt) external returns (bool) {
    uint256 oldValue = _allowance[msg.sender][dst];
    if (amt > oldValue) {
      _allowance[msg.sender][dst] = 0;
    } else {
      _allowance[msg.sender][dst] = bsub(oldValue, amt);
    }
    emit Approval(msg.sender, dst, _allowance[msg.sender][dst]);
    return true;
  }

  function transfer(address dst, uint256 amt) external override returns (bool) {
    _move(msg.sender, dst, amt);
    return true;
  }

  function transferFrom(
    address src,
    address dst,
    uint256 amt
  ) external override returns (bool) {
    require(
      msg.sender == src || amt <= _allowance[src][msg.sender],
      "ERR_BTOKEN_BAD_CALLER"
    );
    _move(src, dst, amt);
    if (msg.sender != src && _allowance[src][msg.sender] != uint256(-1)) {
      _allowance[src][msg.sender] = bsub(_allowance[src][msg.sender], amt);
      emit Approval(msg.sender, dst, _allowance[src][msg.sender]);
    }
    return true;
  }
}