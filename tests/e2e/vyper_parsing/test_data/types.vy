name: public(String[64])
symbol: public(String[32])
decimals: public(uint256)
totalSupply: public(uint256)

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]

MAX_BANDS: constant(uint256) = 10

x: public(uint256[3][4])
y: public(uint256[2])

struct Loan:
    liquidation_range: DynArray[uint256, MAX_BANDS]
    deposit_amounts: DynArray[uint256, MAX_BANDS]