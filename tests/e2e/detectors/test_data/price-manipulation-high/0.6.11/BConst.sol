// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.6.0;


/************************************************************************************************
Originally from https://github.com/balancer-labs/balancer-core/blob/master/contracts/BConst.sol

This source code has been modified from the original, which was copied from the github repository
at commit hash f4ed5d65362a8d6cec21662fb6eae233b0babc1f.

Subject to the GPL-3.0 license
*************************************************************************************************/


contract BConst {
  uint256 public constant VERSION_NUMBER = 1;

/* ---  Weight Updates  --- */

  // Minimum time passed between each weight update for a token.
  uint256 internal constant WEIGHT_UPDATE_DELAY = 30 minutes;

  // Maximum percent by which a weight can adjust at a time
  // relative to the current weight.
  // The number of iterations needed to move from weight A to weight B is the floor of:
  // (A > B): (ln(A) - ln(B)) / ln(1.01)
  // (B > A): (ln(A) - ln(B)) / ln(0.99)
  uint256 internal constant WEIGHT_CHANGE_PCT = BONE/100;

  uint256 internal constant BONE = 10**18;

  uint256 internal constant MIN_BOUND_TOKENS = 2;
  uint256 internal constant MAX_BOUND_TOKENS = 10;

  // Minimum swap fee.
  uint256 internal constant MIN_FEE = BONE / 10**6;
  // Maximum swap or exit fee.
  uint256 internal constant MAX_FEE = BONE / 10;
  // Actual exit fee.
  uint256 internal constant EXIT_FEE = 5e15;

  // Default total of all desired weights. Can differ by up to BONE.
  uint256 internal constant DEFAULT_TOTAL_WEIGHT = BONE * 25;
  // Minimum weight for any token (1/100).
  uint256 internal constant MIN_WEIGHT = BONE / 4;
  uint256 internal constant MAX_WEIGHT = BONE * 25;
  // Maximum total weight.
  uint256 internal constant MAX_TOTAL_WEIGHT = BONE * 27;
  // Minimum balance for a token (only applied at initialization)
  uint256 internal constant MIN_BALANCE = BONE / 10**12;
  // Initial pool tokens
  uint256 internal constant INIT_POOL_SUPPLY = BONE * 100;

  uint256 internal constant MIN_BPOW_BASE = 1 wei;
  uint256 internal constant MAX_BPOW_BASE = (2 * BONE) - 1 wei;
  uint256 internal constant BPOW_PRECISION = BONE / 10**10;

  // Maximum ratio of input tokens to balance for swaps.
  uint256 internal constant MAX_IN_RATIO = BONE / 2;
  // Maximum ratio of output tokens to balance for swaps.
  uint256 internal constant MAX_OUT_RATIO = (BONE / 3) + 1 wei;
}