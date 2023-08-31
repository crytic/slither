interface LMGauge:
    def callback_collateral_shares(n: int256, collateral_per_share: DynArray[uint256, MAX_TICKS_UINT]): nonpayable
    def callback_user_shares(user: address, n: int256, user_shares: DynArray[uint256, MAX_TICKS_UINT]): nonpayable


MAX_TICKS_UINT: constant(uint256) =  50


struct Loan:
    liquidation_range: LMGauge

x: public(Loan)


# TODO Will this overly complicate analyzing AST https://github.com/vyperlang/vyper/pull/3411