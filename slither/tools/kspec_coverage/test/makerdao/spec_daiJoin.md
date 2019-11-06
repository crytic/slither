```act
behaviour vat of DaiJoin
interface vat()

for all

    Vat : address VatLike

storage

    vat |-> Vat

iff

    VCallValue == 0

returns Vat
```

#### dai address

```act
behaviour dai of DaiJoin
interface dai()

for all

    Dai : address

storage

    dai |-> Dai

iff

    VCallValue == 0

returns Dai
```

### Mutators

#### depositing into the system

```act
behaviour muluu of DaiJoin
interface mul(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : x * y : WS

iff in range uint256

    x * y

if

    // TODO: strengthen
    #sizeWordStack(WS) <= 1000
```

```act
behaviour join of DaiJoin
interface join(address usr, uint256 wad)

for all

    Vat     : address VatLike
    Dai     : address Dai
    Supply  : uint256
    Dai_c   : uint256
    Dai_a   : uint256
    Dai_u   : uint256
    Allowed : uint256
    Can     : uint256

storage

    vat |-> Vat
    dai |-> Dai

storage Vat

    can[ACCT_ID][ACCT_ID] |-> Can
    dai[ACCT_ID] |-> Dai_a => Dai_a - (#Ray * wad)
    dai[usr]     |-> Dai_u => Dai_u + (#Ray * wad)

storage Dai

    balanceOf[CALLER_ID]          |-> Dai_c   => Dai_c - wad
    totalSupply                   |-> Supply  => Supply - wad
    allowance[CALLER_ID][ACCT_ID] |-> Allowed => #if Allowed == maxUInt256 #then Allowed #else Allowed - wad #fi

iff

    VCallValue == 0
    VCallDepth < 1024
    (Allowed == maxUInt256) or (wad <= Allowed)

iff in range uint256

    #Ray * wad
    Dai_a - #Ray * wad
    Dai_u + #Ray * wad
    Dai_c - wad
    Supply - wad

if

    ACCT_ID =/= CALLER_ID
    ACCT_ID =/= usr

calls

    DaiJoin.muluu
    Vat.move-diff
    Dai.burn
```

#### withdrawing from the system

```act
behaviour exit of DaiJoin
interface exit(address usr, uint256 wad)

for all

    Vat    : address VatLike
    Dai    : address Dai
    May    : uint256
    Can    : uint256
    Dai_c  : uint256
    Dai_u  : uint256
    Dai_a  : uint256
    Supply : uint256

storage

    vat |-> Vat
    dai |-> Dai

storage Vat

    can[CALLER_ID][ACCT_ID] |-> Can
    dai[CALLER_ID] |-> Dai_c => Dai_c - #Ray * wad
    dai[ACCT_ID]   |-> Dai_a => Dai_a + #Ray * wad

storage Dai

    wards[ACCT_ID] |-> May
    balanceOf[usr] |-> Dai_u  => Dai_u  + wad
    totalSupply    |-> Supply => Supply + wad

iff

    // act: caller is `. ? : not` authorised
    May == 1
    Can == 1
    // act: call stack is not too big
    VCallDepth < 1024
    VCallValue == 0

iff in range uint256

    #Ray * wad
    Dai_c - #Ray * wad
    Dai_a + #Ray * wad
    Dai_u + wad
    Supply + wad

if

    CALLER_ID =/= ACCT_ID

calls

    DaiJoin.muluu
    Vat.move-diff
    Dai.mint
```
