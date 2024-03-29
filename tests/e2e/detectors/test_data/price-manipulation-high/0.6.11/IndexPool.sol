// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.6.0;
pragma experimental ABIEncoderV2;

/* ========== Internal Inheritance ========== */
import "./BToken.sol";
import "./BMath.sol";

/* ========== Internal Interfaces ========== */
import "./IIndexPool.sol";
import "./ICompLikeToken.sol";


/************************************************************************************************
Originally from https://github.com/balancer-labs/balancer-core/blob/master/contracts/BPool.sol

This source code has been modified from the original, which was copied from the github repository
at commit hash f4ed5d65362a8d6cec21662fb6eae233b0babc1f.

Subject to the GPL-3.0 license
*************************************************************************************************/


contract IndexPool is BToken, BMath, IIndexPool {
/* ==========  Modifiers  ========== */

  modifier _lock_ {
    require(!_mutex, "ERR_REENTRY");
    _mutex = true;
    _;
    _mutex = false;
  }

  modifier _viewlock_() {
    require(!_mutex, "ERR_REENTRY");
    _;
  }

  modifier _control_ {
    require(msg.sender == _controller, "ERR_NOT_CONTROLLER");
    _;
  }

  modifier _public_ {
    require(_publicSwap, "ERR_NOT_PUBLIC");
    _;
  }

/* ==========  Storage  ========== */

  bool internal _mutex;

  // Account with CONTROL role. Able to modify the swap fee,
  // adjust token weights, bind and unbind tokens and lock
  // public swaps & joins.
  address internal _controller;

  // Contract that handles unbound tokens.
  TokenUnbindHandler internal _unbindHandler;

  // True if PUBLIC can call SWAP & JOIN functions
  bool internal _publicSwap;

  // `setSwapFee` requires CONTROL
  uint256 internal _swapFee;

  // Array of underlying tokens in the pool.
  address[] internal _tokens;

  // Internal records of the pool's underlying tokens
  mapping(address => Record) internal _records;

  // Total denormalized weight of the pool.
  uint256 internal _totalWeight;

  // Minimum balances for tokens which have been added without the
  // requisite initial balance.
  mapping(address => uint256) internal _minimumBalances;

  // Recipient for exit fees
  address internal _exitFeeRecipient;

/* ==========  Controls  ========== */

  /**
   * @dev Sets the controller address and the token name & symbol.
   *
   * Note: This saves on storage costs for multi-step pool deployment.
   *
   * @param controller Controller of the pool
   * @param name Name of the pool token
   * @param symbol Symbol of the pool token
   * @param exitFeeRecipient Address that receives exit fees
   */
  function configure(
    address controller,
    string calldata name,
    string calldata symbol,
    address exitFeeRecipient
  ) external override {
    require(_controller == address(0), "ERR_CONFIGURED");
    require(controller != address(0) && exitFeeRecipient != address(0), "ERR_NULL_ADDRESS");
    _controller = controller;
    // default fee is 2%
    _swapFee = BONE / 50;
    _exitFeeRecipient = exitFeeRecipient;
    _initializeToken(name, symbol);
  }

  /**
   * @dev Sets up the initial assets for the pool.
   *
   * Note: `tokenProvider` must have approved the pool to transfer the
   * corresponding `balances` of `tokens`.
   *
   * @param tokens Underlying tokens to initialize the pool with
   * @param balances Initial balances to transfer
   * @param denorms Initial denormalized weights for the tokens
   * @param tokenProvider Address to transfer the balances from
   */
  function initialize(
    address[] calldata tokens,
    uint256[] calldata balances,
    uint96[] calldata denorms,
    address tokenProvider,
    address unbindHandler
  )
    external
    override
    _control_
  {
    require(_tokens.length == 0, "ERR_INITIALIZED");
    uint256 len = tokens.length;
    require(len >= MIN_BOUND_TOKENS, "ERR_MIN_TOKENS");
    require(len <= MAX_BOUND_TOKENS, "ERR_MAX_TOKENS");
    require(balances.length == len && denorms.length == len, "ERR_ARR_LEN");
    uint256 totalWeight = 0;
    for (uint256 i = 0; i < len; i++) {
      address token = tokens[i];
      uint96 denorm = denorms[i];
      uint256 balance = balances[i];
      require(denorm >= MIN_WEIGHT, "ERR_MIN_WEIGHT");
      require(denorm <= MAX_WEIGHT, "ERR_MAX_WEIGHT");
      require(balance >= MIN_BALANCE, "ERR_MIN_BALANCE");
      _records[token] = Record({
        bound: true,
        ready: true,
        lastDenormUpdate: uint40(now),
        denorm: denorm,
        desiredDenorm: denorm,
        index: uint8(i),
        balance: balance
      });
      _tokens.push(token);
      totalWeight = badd(totalWeight, denorm);
      _pullUnderlying(token, tokenProvider, balance);
    }
    require(totalWeight <= MAX_TOTAL_WEIGHT, "ERR_MAX_TOTAL_WEIGHT");
    _totalWeight = totalWeight;
    _publicSwap = true;
    emit LOG_PUBLIC_SWAP_ENABLED();
    _mintPoolShare(INIT_POOL_SUPPLY);
    _pushPoolShare(tokenProvider, INIT_POOL_SUPPLY);
    _unbindHandler = TokenUnbindHandler(unbindHandler);
  }

  /**
   * @dev Set the swap fee.
   * Note: Swap fee must be between 0.0001% and 10%
   */
  function setSwapFee(uint256 swapFee) external override _control_ {
    require(swapFee >= MIN_FEE && swapFee <= MAX_FEE, "ERR_INVALID_FEE");
    _swapFee = swapFee;
    emit LOG_SWAP_FEE_UPDATED(swapFee);
  }

  /**
   * @dev Delegate a comp-like governance token to an address
   * specified by the controller.
   */
  function delegateCompLikeToken(address token,address delegatee)
    external
    override
    _control_
  {
    ICompLikeToken(token).delegate(delegatee);
  }

  /**
   * @dev Set the exit fee recipient address.
   */
  function setExitFeeRecipient(address exitFeeRecipient) external override _control_ {
    require(exitFeeRecipient != address(0), "ERR_NULL_ADDRESS");
    _exitFeeRecipient = exitFeeRecipient;
    emit LOG_EXIT_FEE_RECIPIENT_UPDATED(exitFeeRecipient);
  }

  /**
   * @dev Set the controller address
   */
  function setController(address controller) external override _control_ {
    require(controller != address(0), "ERR_NULL_ADDRESS");
    _controller = controller;
    emit LOG_CONTROLLER_UPDATED(controller);
  }

/* ==========  Token Management Actions  ========== */

  /**
   * @dev Sets the desired weights for the pool tokens, which
   * will be adjusted over time as they are swapped.
   *
   * Note: This does not check for duplicate tokens or that the total
   * of the desired weights is equal to the target total weight (25).
   * Those assumptions should be met in the controller. Further, the
   * provided tokens should only include the tokens which are not set
   * for removal.
   */
  function reweighTokens(
    address[] calldata tokens,
    uint96[] calldata desiredDenorms
  )
    external
    override
    _lock_
    _control_
  {
    require(desiredDenorms.length == tokens.length, "ERR_ARR_LEN");
    for (uint256 i = 0; i < tokens.length; i++)
      _setDesiredDenorm(tokens[i], desiredDenorms[i]);
  }

  /**
   * @dev Update the underlying assets held by the pool and their associated
   * weights. Tokens which are not currently bound will be gradually added
   * as they are swapped in to reach the provided minimum balances, which must
   * be an amount of tokens worth the minimum weight of the total pool value.
   * If a currently bound token is not received in this call, the token's
   * desired weight will be set to 0.
   */
  function reindexTokens(
    address[] calldata tokens,
    uint96[] calldata desiredDenorms,
    uint256[] calldata minimumBalances
  )
    external
    override
    _lock_
    _control_
  {
    require(
      desiredDenorms.length == tokens.length && minimumBalances.length == tokens.length,
      "ERR_ARR_LEN"
    );
    // This size may not be the same as the input size, as it is possible
    // to temporarily exceed the index size while tokens are being phased in
    // or out.
    uint256 tLen = _tokens.length;
    bool[] memory receivedIndices = new bool[](tLen);
    // We need to read token records in two separate loops, so
    // write them to memory to avoid duplicate storage reads.
    Record[] memory records = new Record[](tokens.length);
    // Read all the records from storage and mark which of the existing tokens
    // were represented in the reindex call.
    for (uint256 i = 0; i < tokens.length; i++) {
      records[i] = _records[tokens[i]];
      if (records[i].bound) receivedIndices[records[i].index] = true;
    }
    // If any bound tokens were not sent in this call, set their desired weights to 0.
    for (uint256 i = 0; i < tLen; i++) {
      if (!receivedIndices[i]) {
        _setDesiredDenorm(_tokens[i], 0);
      }
    }
    for (uint256 i = 0; i < tokens.length; i++) {
      address token = tokens[i];
      // If an input weight is less than the minimum weight, use that instead.
      uint96 denorm = desiredDenorms[i];
      if (denorm < MIN_WEIGHT) denorm = uint96(MIN_WEIGHT);
      if (!records[i].bound) {
        // If the token is not bound, bind it.
        _bind(token, minimumBalances[i], denorm);
      } else {
        _setDesiredDenorm(token, denorm);
      }
    }
  }

  /**
   * @dev Updates the minimum balance for an uninitialized token.
   * This becomes useful if a token's external price significantly
   * rises after being bound, since the pool can not send a token
   * out until it reaches the minimum balance.
   */
  function setMinimumBalance(
    address token,
    uint256 minimumBalance
  )
    external
    override
    _control_
  {
    Record storage record = _records[token];
    require(record.bound, "ERR_NOT_BOUND");
    require(!record.ready, "ERR_READY");
    _minimumBalances[token] = minimumBalance;
    emit LOG_MINIMUM_BALANCE_UPDATED(token, minimumBalance);
  }

/* ==========  Liquidity Provider Actions  ========== */

  /**
   * @dev Mint new pool tokens by providing the proportional amount of each
   * underlying token's balance relative to the proportion of pool tokens minted.
   *
   * For any underlying tokens which are not initialized, the caller must provide
   * the proportional share of the minimum balance for the token rather than the
   * actual balance.
   *
   * @param poolAmountOut Amount of pool tokens to mint
   * @param maxAmountsIn Maximum amount of each token to pay in the same
   * order as the pool's _tokens list.
   */
  function joinPool(uint256 poolAmountOut, uint256[] calldata maxAmountsIn)
    external
    override
    _lock_
    _public_
  {
    uint256 poolTotal = totalSupply();
    uint256 ratio = bdiv(poolAmountOut, poolTotal);
    require(ratio != 0, "ERR_MATH_APPROX");
    require(maxAmountsIn.length == _tokens.length, "ERR_ARR_LEN");

    for (uint256 i = 0; i < maxAmountsIn.length; i++) {
      address t = _tokens[i];
      (Record memory record, uint256 realBalance) = _getInputToken(t);
      uint256 tokenAmountIn = bmul(ratio, record.balance);
      require(tokenAmountIn != 0, "ERR_MATH_APPROX");
      require(tokenAmountIn <= maxAmountsIn[i], "ERR_LIMIT_IN");
      _updateInputToken(t, record, badd(realBalance, tokenAmountIn));
      emit LOG_JOIN(msg.sender, t, tokenAmountIn);
      _pullUnderlying(t, msg.sender, tokenAmountIn);
    }
    _mintPoolShare(poolAmountOut);
    _pushPoolShare(msg.sender, poolAmountOut);
  }

  /**
   * @dev Pay `tokenAmountIn` of `tokenIn` to mint at least `minPoolAmountOut`
   * pool tokens.
   *
   * The pool implicitly swaps `(1- weightTokenIn) * tokenAmountIn` to the other
   * underlying tokens. Thus a swap fee is charged against the input tokens.
   *
   * @param tokenIn Token to send the pool
   * @param tokenAmountIn Exact amount of `tokenIn` to pay
   * @param minPoolAmountOut Minimum amount of pool tokens to mint
   * @return poolAmountOut - Amount of pool tokens minted
   */
  function joinswapExternAmountIn(
    address tokenIn,
    uint256 tokenAmountIn,
    uint256 minPoolAmountOut
  )
    external
    override
    _lock_
    _public_
    returns (uint256/* poolAmountOut */)
  {
    (Record memory inRecord, uint256 realInBalance) = _getInputToken(tokenIn);

    require(tokenAmountIn != 0, "ERR_ZERO_IN");

    require(
      tokenAmountIn <= bmul(inRecord.balance, MAX_IN_RATIO),
      "ERR_MAX_IN_RATIO"
    );

    uint256 poolAmountOut = calcPoolOutGivenSingleIn(
      inRecord.balance,
      inRecord.denorm,
      _totalSupply,
      _totalWeight,
      tokenAmountIn,
      _swapFee
    );

    require(poolAmountOut >= minPoolAmountOut, "ERR_LIMIT_OUT");

    _updateInputToken(tokenIn, inRecord, badd(realInBalance, tokenAmountIn));

    emit LOG_JOIN(msg.sender, tokenIn, tokenAmountIn);

    _mintPoolShare(poolAmountOut);
    _pushPoolShare(msg.sender, poolAmountOut);
    _pullUnderlying(tokenIn, msg.sender, tokenAmountIn);

    return poolAmountOut;
  }

  /**
   * @dev Pay up to `maxAmountIn` of `tokenIn` to mint exactly `poolAmountOut`.
   *
   * The pool implicitly swaps `(1- weightTokenIn) * tokenAmountIn` to the other
   * underlying tokens. Thus a swap fee is charged against the input tokens.
   *
   * @param tokenIn Token to send the pool
   * @param poolAmountOut Exact amount of pool tokens to mint
   * @param maxAmountIn Maximum amount of `tokenIn` to pay
   * @return tokenAmountIn - Amount of `tokenIn` paid
   */
  function joinswapPoolAmountOut(
    address tokenIn,
    uint256 poolAmountOut,
    uint256 maxAmountIn
  )
    external
    override
    _lock_
    _public_
    returns (uint256/* tokenAmountIn */)
  {
    (Record memory inRecord, uint256 realInBalance) = _getInputToken(tokenIn);

    uint256 tokenAmountIn = calcSingleInGivenPoolOut(
      inRecord.balance,
      inRecord.denorm,
      _totalSupply,
      _totalWeight,
      poolAmountOut,
      _swapFee
    );

    require(tokenAmountIn != 0, "ERR_MATH_APPROX");
    require(tokenAmountIn <= maxAmountIn, "ERR_LIMIT_IN");

    require(
      tokenAmountIn <= bmul(inRecord.balance, MAX_IN_RATIO),
      "ERR_MAX_IN_RATIO"
    );

    _updateInputToken(tokenIn, inRecord, badd(realInBalance, tokenAmountIn));

    emit LOG_JOIN(msg.sender, tokenIn, tokenAmountIn);

    _mintPoolShare(poolAmountOut);
    _pushPoolShare(msg.sender, poolAmountOut);
    _pullUnderlying(tokenIn, msg.sender, tokenAmountIn);

    return tokenAmountIn;
  }

  /**
   * @dev Burns `poolAmountIn` pool tokens in exchange for the amounts of each
   * underlying token's balance proportional to the ratio of tokens burned to
   * total pool supply. The amount of each token transferred to the caller must
   * be greater than or equal to the associated minimum output amount from the
   * `minAmountsOut` array.
   *
   * @param poolAmountIn Exact amount of pool tokens to burn
   * @param minAmountsOut Minimum amount of each token to receive, in the same
   * order as the pool's _tokens list.
   */
  function exitPool(uint256 poolAmountIn, uint256[] calldata minAmountsOut)
    external
    override
    _lock_
  {
    require(minAmountsOut.length == _tokens.length, "ERR_ARR_LEN");
    uint256 poolTotal = totalSupply();
    uint256 exitFee = bmul(poolAmountIn, EXIT_FEE);
    uint256 pAiAfterExitFee = bsub(poolAmountIn, exitFee);
    uint256 ratio = bdiv(pAiAfterExitFee, poolTotal);
    require(ratio != 0, "ERR_MATH_APPROX");

    _pullPoolShare(msg.sender, poolAmountIn);
    _pushPoolShare(_exitFeeRecipient, exitFee);
    _burnPoolShare(pAiAfterExitFee);
    for (uint256 i = 0; i < minAmountsOut.length; i++) {
      address t = _tokens[i];
      Record memory record = _records[t];
      if (record.ready) {
        uint256 tokenAmountOut = bmul(ratio, record.balance);
        require(tokenAmountOut != 0, "ERR_MATH_APPROX");
        require(tokenAmountOut >= minAmountsOut[i], "ERR_LIMIT_OUT");

        _records[t].balance = bsub(record.balance, tokenAmountOut);
        emit LOG_EXIT(msg.sender, t, tokenAmountOut);
        _pushUnderlying(t, msg.sender, tokenAmountOut);
      } else {
        // If the token is not initialized, it can not exit the pool.
        require(minAmountsOut[i] == 0, "ERR_OUT_NOT_READY");
      }
    }
  }

  /**
   * @dev Burns `poolAmountIn` pool tokens in exchange for at least `minAmountOut`
   * of `tokenOut`. Returns the number of tokens sent to the caller.
   *
   * The pool implicitly burns the tokens for all underlying tokens and swaps them
   * to the desired output token. A swap fee is charged against the output tokens.
   *
   * @param tokenOut Token to receive
   * @param poolAmountIn Exact amount of pool tokens to burn
   * @param minAmountOut Minimum amount of `tokenOut` to receive
   * @return tokenAmountOut - Amount of `tokenOut` received
   */
  function exitswapPoolAmountIn(
    address tokenOut,
    uint256 poolAmountIn,
    uint256 minAmountOut
  )
    external
    override
    _lock_
    returns (uint256/* tokenAmountOut */)
  {
    Record memory outRecord = _getOutputToken(tokenOut);

    uint256 tokenAmountOut = calcSingleOutGivenPoolIn(
      outRecord.balance,
      outRecord.denorm,
      _totalSupply,
      _totalWeight,
      poolAmountIn,
      _swapFee
    );

    require(tokenAmountOut >= minAmountOut, "ERR_LIMIT_OUT");

    require(
      tokenAmountOut <= bmul(outRecord.balance, MAX_OUT_RATIO),
      "ERR_MAX_OUT_RATIO"
    );

    _pushUnderlying(tokenOut, msg.sender, tokenAmountOut);
    _records[tokenOut].balance = bsub(outRecord.balance, tokenAmountOut);
    _decreaseDenorm(outRecord, tokenOut);
    uint256 exitFee = bmul(poolAmountIn, EXIT_FEE);

    emit LOG_EXIT(msg.sender, tokenOut, tokenAmountOut);

    _pullPoolShare(msg.sender, poolAmountIn);
    _burnPoolShare(bsub(poolAmountIn, exitFee));
    _pushPoolShare(_exitFeeRecipient, exitFee);

    return tokenAmountOut;
  }

  /**
   * @dev Burn up to `maxPoolAmountIn` for exactly `tokenAmountOut` of `tokenOut`.
   * Returns the number of pool tokens burned.
   *
   * The pool implicitly burns the tokens for all underlying tokens and swaps them
   * to the desired output token. A swap fee is charged against the output tokens.
   *
   * @param tokenOut Token to receive
   * @param tokenAmountOut Exact amount of `tokenOut` to receive
   * @param maxPoolAmountIn Maximum amount of pool tokens to burn
   * @return poolAmountIn - Amount of pool tokens burned
   */
  function exitswapExternAmountOut(
    address tokenOut,
    uint256 tokenAmountOut,
    uint256 maxPoolAmountIn
  )
    external
    override
    _lock_
    returns (uint256/* poolAmountIn */)
  {
    Record memory outRecord = _getOutputToken(tokenOut);
    require(
      tokenAmountOut <= bmul(outRecord.balance, MAX_OUT_RATIO),
      "ERR_MAX_OUT_RATIO"
    );

    uint256 poolAmountIn = calcPoolInGivenSingleOut(
      outRecord.balance,
      outRecord.denorm,
      _totalSupply,
      _totalWeight,
      tokenAmountOut,
      _swapFee
    );

    require(poolAmountIn != 0, "ERR_MATH_APPROX");
    require(poolAmountIn <= maxPoolAmountIn, "ERR_LIMIT_IN");

    _pushUnderlying(tokenOut, msg.sender, tokenAmountOut);
    _records[tokenOut].balance = bsub(outRecord.balance, tokenAmountOut);
    _decreaseDenorm(outRecord, tokenOut);

    uint256 exitFee = bmul(poolAmountIn, EXIT_FEE);

    emit LOG_EXIT(msg.sender, tokenOut, tokenAmountOut);

    _pullPoolShare(msg.sender, poolAmountIn);
    _burnPoolShare(bsub(poolAmountIn, exitFee));
    _pushPoolShare(_exitFeeRecipient, exitFee);

    return poolAmountIn;
  }

/* ==========  Other  ========== */

  /**
   * @dev Absorb any tokens that have been sent to the pool.
   * If the token is not bound, it will be sent to the unbound
   * token handler.
   */
  function gulp(address token) external override _lock_ {
    Record storage record = _records[token];
    uint256 balance = IERC20(token).balanceOf(address(this));
    if (record.bound) {
      if (!record.ready) {
        uint256 minimumBalance = _minimumBalances[token];
        if (balance >= minimumBalance) {
          _minimumBalances[token] = 0;
          record.ready = true;
          emit LOG_TOKEN_READY(token);
          uint256 additionalBalance = bsub(balance, minimumBalance);
          uint256 balRatio = bdiv(additionalBalance, minimumBalance);
          uint96 newDenorm = uint96(badd(MIN_WEIGHT, bmul(MIN_WEIGHT, balRatio)));
          record.denorm = newDenorm;
          record.lastDenormUpdate = uint40(now);
          _totalWeight = badd(_totalWeight, newDenorm);
          emit LOG_DENORM_UPDATED(token, record.denorm);
        }
      }
      _records[token].balance = balance;
    } else {
      _pushUnderlying(token, address(_unbindHandler), balance);
      _unbindHandler.handleUnbindToken(token, balance);
    }
  }

/* ==========  Token Swaps  ========== */

  /**
   * @dev Execute a token swap with a specified amount of input
   * tokens and a minimum amount of output tokens.
   *
   * Note: Will revert if `tokenOut` is uninitialized.
   *
   * @param tokenIn Token to swap in
   * @param tokenAmountIn Exact amount of `tokenIn` to swap in
   * @param tokenOut Token to swap out
   * @param minAmountOut Minimum amount of `tokenOut` to receive
   * @param maxPrice Maximum ratio of input to output tokens
   * @return (tokenAmountOut, spotPriceAfter)
   */
  function swapExactAmountIn(
    address tokenIn,
    uint256 tokenAmountIn,
    address tokenOut,
    uint256 minAmountOut,
    uint256 maxPrice
  )
    external
    override
    _lock_
    _public_
    returns (uint256/* tokenAmountOut */, uint256/* spotPriceAfter */)
  {
    (Record memory inRecord, uint256 realInBalance) = _getInputToken(tokenIn);
    Record memory outRecord = _getOutputToken(tokenOut);

    require(
      tokenAmountIn <= bmul(inRecord.balance, MAX_IN_RATIO),
      "ERR_MAX_IN_RATIO"
    );

    uint256 spotPriceBefore = calcSpotPrice(
      inRecord.balance,
      inRecord.denorm,
      outRecord.balance,
      outRecord.denorm,
      _swapFee
    );
    require(spotPriceBefore <= maxPrice, "ERR_BAD_LIMIT_PRICE");

    uint256 tokenAmountOut = calcOutGivenIn(
      inRecord.balance,
      inRecord.denorm,
      outRecord.balance,
      outRecord.denorm,
      tokenAmountIn,
      _swapFee
    );

    require(tokenAmountOut >= minAmountOut, "ERR_LIMIT_OUT");

    _pullUnderlying(tokenIn, msg.sender, tokenAmountIn);
    _pushUnderlying(tokenOut, msg.sender, tokenAmountOut);

    // Update the in-memory record for the spotPriceAfter calculation,
    // then update the storage record with the local balance.
    outRecord.balance = bsub(outRecord.balance, tokenAmountOut);
    _records[tokenOut].balance = outRecord.balance;
    // If needed, update the output token's weight.
    _decreaseDenorm(outRecord, tokenOut);

    realInBalance = badd(realInBalance, tokenAmountIn);
    _updateInputToken(tokenIn, inRecord, realInBalance);
    if (inRecord.ready) {
      inRecord.balance = realInBalance;
    }

    uint256 spotPriceAfter = calcSpotPrice(
      inRecord.balance,
      inRecord.denorm,
      outRecord.balance,
      outRecord.denorm,
      _swapFee
    );

    require(spotPriceAfter >= spotPriceBefore, "ERR_MATH_APPROX_2");
    require(spotPriceAfter <= maxPrice, "ERR_LIMIT_PRICE");
    require(
      spotPriceBefore <= bdiv(tokenAmountIn, tokenAmountOut),
      "ERR_MATH_APPROX"
    );

    emit LOG_SWAP(msg.sender, tokenIn, tokenOut, tokenAmountIn, tokenAmountOut);

    return (tokenAmountOut, spotPriceAfter);
  }

  /**
   * @dev Trades at most `maxAmountIn` of `tokenIn` for exactly `tokenAmountOut`
   * of `tokenOut`.
   *
   * Returns the actual input amount and the new spot price after the swap,
   * which can not exceed `maxPrice`.
   *
   * @param tokenIn Token to swap in
   * @param maxAmountIn Maximum amount of `tokenIn` to pay
   * @param tokenOut Token to swap out
   * @param tokenAmountOut Exact amount of `tokenOut` to receive
   * @param maxPrice Maximum ratio of input to output tokens
   * @return (tokenAmountIn, spotPriceAfter)
   */
  function swapExactAmountOut(
    address tokenIn,
    uint256 maxAmountIn,
    address tokenOut,
    uint256 tokenAmountOut,
    uint256 maxPrice
  )
    external
    override
    _lock_
    _public_
    returns (uint256 /* tokenAmountIn */, uint256 /* spotPriceAfter */)
  {
    (Record memory inRecord, uint256 realInBalance) = _getInputToken(tokenIn);
    Record memory outRecord = _getOutputToken(tokenOut);

    require(
      tokenAmountOut <= bmul(outRecord.balance, MAX_OUT_RATIO),
      "ERR_MAX_OUT_RATIO"
    );

    uint256 spotPriceBefore = calcSpotPrice(
      inRecord.balance,
      inRecord.denorm,
      outRecord.balance,
      outRecord.denorm,
      _swapFee
    );
    require(spotPriceBefore <= maxPrice, "ERR_BAD_LIMIT_PRICE");

    uint256 tokenAmountIn = calcInGivenOut(
      inRecord.balance,
      inRecord.denorm,
      outRecord.balance,
      outRecord.denorm,
      tokenAmountOut,
      _swapFee
    );

    require(tokenAmountIn <= maxAmountIn, "ERR_LIMIT_IN");

    _pullUnderlying(tokenIn, msg.sender, tokenAmountIn);
    _pushUnderlying(tokenOut, msg.sender, tokenAmountOut);

    // Update the in-memory record for the spotPriceAfter calculation,
    // then update the storage record with the local balance.
    outRecord.balance = bsub(outRecord.balance, tokenAmountOut);
    _records[tokenOut].balance = outRecord.balance;
    // If needed, update the output token's weight.
    _decreaseDenorm(outRecord, tokenOut);

    // Update the balance and (if necessary) weight of the input token.
    realInBalance = badd(realInBalance, tokenAmountIn);
    _updateInputToken(tokenIn, inRecord, realInBalance);
    if (inRecord.ready) {
      inRecord.balance = realInBalance;
    }

    uint256 spotPriceAfter = calcSpotPrice(
      inRecord.balance,
      inRecord.denorm,
      outRecord.balance,
      outRecord.denorm,
      _swapFee
    );

    require(spotPriceAfter >= spotPriceBefore, "ERR_MATH_APPROX");
    require(spotPriceAfter <= maxPrice, "ERR_LIMIT_PRICE");
    require(
      spotPriceBefore <= bdiv(tokenAmountIn, tokenAmountOut),
      "ERR_MATH_APPROX"
    );

    emit LOG_SWAP(msg.sender, tokenIn, tokenOut, tokenAmountIn, tokenAmountOut);

    return (tokenAmountIn, spotPriceAfter);
  }

/* ==========  Config Queries  ========== */
  /**
   * @dev Check if swapping tokens and joining the pool is allowed.
   */
  function isPublicSwap() external view override returns (bool) {
    return _publicSwap;
  }

  function getSwapFee() external view override _viewlock_ returns (uint256/* swapFee */) {
    return _swapFee;
  }

  function getExitFee() external view override _viewlock_ returns (uint256/* exitFee */) {
    return EXIT_FEE;
  }

  /**
   * @dev Returns the controller address.
   */
  function getController() external view override returns (address)
  {
    return _controller;
  }

  /**
   * @dev Returns the exit fee recipient address.
   */
  function getExitFeeRecipient() external view override returns (address) {
    return _exitFeeRecipient;
  }

/* ==========  Token Queries  ========== */

  /**
   * @dev Check if a token is bound to the pool.
   */
  function isBound(address t) external view override returns (bool) {
    return _records[t].bound;
  }

  /**
   * @dev Get the number of tokens bound to the pool.
   */
  function getNumTokens() external view override returns (uint256) {
    return _tokens.length;
  }

  /**
   * @dev Get all bound tokens.
   */
  function getCurrentTokens()
    external
    view
    override
    _viewlock_
    returns (address[] memory tokens)
  {
    tokens = _tokens;
  }

  /**
   * @dev Returns the list of tokens which have a desired weight above 0.
   * Tokens with a desired weight of 0 are set to be phased out of the pool.
   */
  function getCurrentDesiredTokens()
    external
    view
    override
    _viewlock_
    returns (address[] memory tokens)
  {
    address[] memory tempTokens = _tokens;
    tokens = new address[](tempTokens.length);
    uint256 usedIndex = 0;
    for (uint256 i = 0; i < tokens.length; i++) {
      address token = tempTokens[i];
      if (_records[token].desiredDenorm > 0) {
        tokens[usedIndex++] = token;
      }
    }
    assembly { mstore(tokens, usedIndex) }
  }

  /**
   * @dev Returns the denormalized weight of a bound token.
   */
  function getDenormalizedWeight(address token)
    external
    view
    override
    _viewlock_
    returns (uint256/* denorm */)
  {
    require(_records[token].bound, "ERR_NOT_BOUND");
    return _records[token].denorm;
  }

  /**
   * @dev Returns the record for a token bound to the pool.
   */
  function getTokenRecord(address token)
    external
    view
    override
    _viewlock_
    returns (Record memory record)
  {
    record = _records[token];
    require(record.bound, "ERR_NOT_BOUND");
  }

  /**
   * @dev Finds the first token which is both initialized and has a
   * desired weight above 0, then returns the address of that token
   * and the extrapolated value of the pool in terms of that token.
   *
   * The value is extrapolated by multiplying the token's
   * balance by the reciprocal of its normalized weight.
   * @return (token, extrapolatedValue)
   */
  function extrapolatePoolValueFromToken()
    external
    view
    override
    _viewlock_
    returns (address/* token */, uint256/* extrapolatedValue */)
  {
    address token;
    uint256 extrapolatedValue;
    uint256 len = _tokens.length;
    for (uint256 i = 0; i < len; i++) {
      token = _tokens[i];
      Record storage record = _records[token];
      if (record.ready && record.desiredDenorm > 0) {
        extrapolatedValue = bmul(
          record.balance,
          bdiv(_totalWeight, record.denorm)
        );
        break;
      }
    }
    require(extrapolatedValue > 0, "ERR_NONE_READY");
    return (token, extrapolatedValue);
  }

  /**
   * @dev Get the total denormalized weight of the pool.
   */
  function getTotalDenormalizedWeight()
    external
    view
    override
    _viewlock_
    returns (uint256)
  {
    return _totalWeight;
  }

  /**
   * @dev Returns the stored balance of a bound token.
   */
  function getBalance(address token) external view override _viewlock_ returns (uint256) {
    Record storage record = _records[token];
    require(record.bound, "ERR_NOT_BOUND");
    return record.balance;
  }

  /**
   * @dev Get the minimum balance of an uninitialized token.
   * Note: Throws if the token is initialized.
   */
  function getMinimumBalance(address token) external view override _viewlock_ returns (uint256) {
    Record memory record = _records[token];
    require(record.bound, "ERR_NOT_BOUND");
    require(!record.ready, "ERR_READY");
    return _minimumBalances[token];
  }

  /**
   * @dev Returns the balance of a token which is used in price
   * calculations. If the token is initialized, this is the
   * stored balance; if not, this is the minimum balance.
   */
  function getUsedBalance(address token) external view override _viewlock_ returns (uint256) {
    Record memory record = _records[token];
    require(record.bound, "ERR_NOT_BOUND");
    if (!record.ready) {
      return _minimumBalances[token];
    }
    return record.balance;
  }

/* ==========  Price Queries  ========== */
  /**
   * @dev Returns the spot price for `tokenOut` in terms of `tokenIn`.
   */
  function getSpotPrice(address tokenIn, address tokenOut)
    external
    view
    override
    _viewlock_
    returns (uint256)
  {
    (Record memory inRecord,) = _getInputToken(tokenIn);
    Record memory outRecord = _getOutputToken(tokenOut);
    return
      calcSpotPrice(
        inRecord.balance,
        inRecord.denorm,
        outRecord.balance,
        outRecord.denorm,
        _swapFee
      );
  }

/* ==========  Pool Share Internal Functions  ========== */

  function _pullPoolShare(address from, uint256 amount) internal {
    _pull(from, amount);
  }

  function _pushPoolShare(address to, uint256 amount) internal {
    _push(to, amount);
  }

  function _mintPoolShare(uint256 amount) internal {
    _mint(amount);
  }

  function _burnPoolShare(uint256 amount) internal {
    _burn(amount);
  }

/* ==========  Underlying Token Internal Functions  ========== */
  // 'Underlying' token-manipulation functions make external calls but are NOT locked
  // You must `_lock_` or otherwise ensure reentry-safety

  function _pullUnderlying(
    address erc20,
    address from,
    uint256 amount
  ) internal {
    (bool success, bytes memory data) = erc20.call(
      abi.encodeWithSelector(
        IERC20.transferFrom.selector,
        from,
        address(this),
        amount
      )
    );
    require(
      success && (data.length == 0 || abi.decode(data, (bool))),
      "ERR_ERC20_FALSE"
    );
  }

  function _pushUnderlying(
    address erc20,
    address to,
    uint256 amount
  ) internal {
    (bool success, bytes memory data) = erc20.call(
      abi.encodeWithSelector(
        IERC20.transfer.selector,
        to,
        amount
      )
    );
    require(
      success && (data.length == 0 || abi.decode(data, (bool))),
      "ERR_ERC20_FALSE"
    );
  }

/* ==========  Token Management Internal Functions  ========== */

  /**
   * @dev Bind a token by address without actually depositing a balance.
   * The token will be unable to be swapped out until it reaches the minimum balance.
   * Note: Token must not already be bound.
   * Note: `minimumBalance` should represent an amount of the token which is worth
   * the portion of the current pool value represented by the minimum weight.
   * @param token Address of the token to bind
   * @param minimumBalance minimum balance to reach before the token can be swapped out
   * @param desiredDenorm Desired weight for the token.
   */
  function _bind(
    address token,
    uint256 minimumBalance,
    uint96 desiredDenorm
  ) internal {
    require(!_records[token].bound, "ERR_IS_BOUND");

    require(desiredDenorm >= MIN_WEIGHT, "ERR_MIN_WEIGHT");
    require(desiredDenorm <= MAX_WEIGHT, "ERR_MAX_WEIGHT");
    require(minimumBalance >= MIN_BALANCE, "ERR_MIN_BALANCE");

    _records[token] = Record({
      bound: true,
      ready: false,
      lastDenormUpdate: 0,
      denorm: 0,
      desiredDenorm: desiredDenorm,
      index: uint8(_tokens.length),
      balance: 0
    });
    _tokens.push(token);
    _minimumBalances[token] = minimumBalance;
    emit LOG_TOKEN_ADDED(token, desiredDenorm, minimumBalance);
  }

  /**
   * @dev Remove a token from the pool.
   * Replaces the address in the tokens array with the last address,
   * then removes it from the array.
   * Note: This should only be called after the total weight has been adjusted.
   * Note: Must be called in a function with:
   * - _lock_ modifier to prevent reentrance
   * - requirement that the token is bound
   */
  function _unbind(address token) internal {
    Record memory record = _records[token];
    uint256 tokenBalance = record.balance;

    // Swap the token-to-unbind with the last token,
    // then delete the last token
    uint256 index = record.index;
    uint256 last = _tokens.length - 1;
    // Only swap the token with the last token if it is not
    // already at the end of the array.
    if (index != last) {
      _tokens[index] = _tokens[last];
      _records[_tokens[index]].index = uint8(index);
    }
    _tokens.pop();
    _records[token] = Record({
      bound: false,
      ready: false,
      lastDenormUpdate: 0,
      denorm: 0,
      desiredDenorm: 0,
      index: 0,
      balance: 0
    });
    // transfer any remaining tokens out
    _pushUnderlying(token, address(_unbindHandler), tokenBalance);
    _unbindHandler.handleUnbindToken(token, tokenBalance);
    emit LOG_TOKEN_REMOVED(token);
  }

  function _setDesiredDenorm(address token, uint96 desiredDenorm) internal {
    Record storage record = _records[token];
    require(record.bound, "ERR_NOT_BOUND");
    // If the desired weight is 0, this will trigger a gradual unbinding of the token.
    // Therefore the weight only needs to be above the minimum weight if it isn't 0.
    require(
      desiredDenorm >= MIN_WEIGHT || desiredDenorm == 0,
      "ERR_MIN_WEIGHT"
    );
    require(desiredDenorm <= MAX_WEIGHT, "ERR_MAX_WEIGHT");
    record.desiredDenorm = desiredDenorm;
    emit LOG_DESIRED_DENORM_SET(token, desiredDenorm);
  }

  function _increaseDenorm(Record memory record, address token) internal {
    // If the weight does not need to increase or the token is not
    // initialized, don't do anything.
    if (
      record.denorm >= record.desiredDenorm ||
      !record.ready ||
      now - record.lastDenormUpdate < WEIGHT_UPDATE_DELAY
    ) return;
    uint96 oldWeight = record.denorm;
    uint96 denorm = record.desiredDenorm;
    uint256 maxDiff = bmul(oldWeight, WEIGHT_CHANGE_PCT);
    uint256 diff = bsub(denorm, oldWeight);
    if (diff > maxDiff) {
      denorm = uint96(badd(oldWeight, maxDiff));
      diff = maxDiff;
    }
    // If new total weight exceeds the maximum, do not update
    uint256 newTotalWeight = badd(_totalWeight, diff);
    if (newTotalWeight > MAX_TOTAL_WEIGHT) return;
    _totalWeight = newTotalWeight;
    // Update the in-memory denorm value for spot-price computations.
    record.denorm = denorm;
    // Update the storage record
    _records[token].denorm = denorm;
    _records[token].lastDenormUpdate = uint40(now);
    emit LOG_DENORM_UPDATED(token, denorm);
  }

  function _decreaseDenorm(Record memory record, address token) internal {
    // If the weight does not need to decrease, don't do anything.
    if (
      record.denorm <= record.desiredDenorm ||
      !record.ready ||
      now - record.lastDenormUpdate < WEIGHT_UPDATE_DELAY
    ) return;
    uint96 oldWeight = record.denorm;
    uint96 denorm = record.desiredDenorm;
    uint256 maxDiff = bmul(oldWeight, WEIGHT_CHANGE_PCT);
    uint256 diff = bsub(oldWeight, denorm);
    if (diff > maxDiff) {
      denorm = uint96(bsub(oldWeight, maxDiff));
      diff = maxDiff;
    }
    if (denorm <= MIN_WEIGHT) {
      denorm = 0;
      _totalWeight = bsub(_totalWeight, denorm);
      // Because this is removing the token from the pool, the
      // in-memory denorm value is irrelevant, as it is only used
      // to calculate the new spot price, but the spot price calc
      // will throw if it is passed 0 for the denorm.
      _unbind(token);
    } else {
      _totalWeight = bsub(_totalWeight, diff);
      // Update the in-memory denorm value for spot-price computations.
      record.denorm = denorm;
      // Update the stored denorm value
      _records[token].denorm = denorm;
      _records[token].lastDenormUpdate = uint40(now);
      emit LOG_DENORM_UPDATED(token, denorm);
    }
  }

  /**
   * @dev Handles weight changes and initialization of an
   * input token.
   *
   * If the token is not initialized and the new balance is
   * still below the minimum, this will not do anything.
   *
   * If the token is not initialized but the new balance will
   * bring the token above the minimum balance, this will
   * mark the token as initialized, remove the minimum
   * balance and set the weight to the minimum weight plus
   * 1%.
   *
   *
   * @param token Address of the input token
   * @param record Token record with minimums applied to the balance
   * and weight if the token was uninitialized.
   */
  function _updateInputToken(
    address token,
    Record memory record,
    uint256 realBalance
  )
    internal
  {
    if (!record.ready) {
      // Check if the minimum balance has been reached
      if (realBalance >= record.balance) {
        // Remove the minimum balance record
        _minimumBalances[token] = 0;
        // Mark the token as initialized
        _records[token].ready = true;
        record.ready = true;
        emit LOG_TOKEN_READY(token);
        // Set the initial denorm value to the minimum weight times one plus
        // the ratio of the increase in balance over the minimum to the minimum
        // balance.
        // weight = (1 + ((bal - min_bal) / min_bal)) * min_weight
        uint256 additionalBalance = bsub(realBalance, record.balance);
        uint256 balRatio = bdiv(additionalBalance, record.balance);
        record.denorm = uint96(badd(MIN_WEIGHT, bmul(MIN_WEIGHT, balRatio)));
        _records[token].denorm = record.denorm;
        _records[token].lastDenormUpdate = uint40(now);
        _totalWeight = badd(_totalWeight, record.denorm);
        emit LOG_DENORM_UPDATED(token, record.denorm);
      } else {
        uint256 realToMinRatio = bdiv(
          bsub(record.balance, realBalance),
          record.balance
        );
        uint256 weightPremium = bmul(MIN_WEIGHT / 10, realToMinRatio);
        record.denorm = uint96(badd(MIN_WEIGHT, weightPremium));
      }
      // If the token is still not ready, do not adjust the weight.
    } else {
      // If the token is already initialized, update the weight (if any adjustment
      // is needed).
      _increaseDenorm(record, token);
    }
    // Regardless of whether the token is initialized, store the actual new balance.
    _records[token].balance = realBalance;
  }

/* ==========  Token Query Internal Functions  ========== */

  /**
   * @dev Get the record for a token which is being swapped in.
   * The token must be bound to the pool. If the token is not
   * initialized (meaning it does not have the minimum balance)
   * this function will return the actual balance of the token
   * which the pool holds, but set the record's balance and weight
   * to the token's minimum balance and the pool's minimum weight.
   * This allows the token swap to be priced correctly even if the
   * pool does not own any of the tokens.
   */
  function _getInputToken(address token)
    internal
    view
    returns (Record memory record, uint256 realBalance)
  {
    record = _records[token];
    require(record.bound, "ERR_NOT_BOUND");

    realBalance = record.balance;
    // If the input token is not initialized, we use the minimum
    // initial weight and minimum initial balance instead of the
    // real values for price and output calculations.
    if (!record.ready) {
      record.balance = _minimumBalances[token];
      uint256 realToMinRatio = bdiv(
        bsub(record.balance, realBalance),
        record.balance
      );
      uint256 weightPremium = bmul(MIN_WEIGHT / 10, realToMinRatio);
      record.denorm = uint96(badd(MIN_WEIGHT, weightPremium));
    }
  }

  function _getOutputToken(address token)
    internal
    view
    returns (Record memory record)
  {
    record = _records[token];
    require(record.bound, "ERR_NOT_BOUND");
    // Tokens which have not reached their minimum balance can not be
    // swapped out.
    require(record.ready, "ERR_OUT_NOT_READY");
  }
}


interface TokenUnbindHandler {
  /**
   * @dev Receive `amount` of `token` from the pool.
   */
  function handleUnbindToken(address token, uint256 amount) external;
}