```act
behaviour wards of Flopper
interface wards(address usr)

for all

    May : uint256

storage

    wards[usr] |-> May

iff

    VCallValue == 0

returns May
```



#### bid data

```act
behaviour bids of Flopper
interface bids(uint256 n)

for all

    Bid : uint256
    Lot : uint256
    Guy : address
    Tic : uint48
    End : uint48

storage

    bids[n].bid         |-> Bid
    bids[n].lot         |-> Lot
    bids[n].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End)

iff

    VCallValue == 0

returns Bid : Lot : Guy : Tic : End
```

#### CDP Engine

```act
behaviour vat of Flopper
interface vat()

for all

    Vat : address

storage

    vat |-> Vat

iff

    VCallValue == 0

returns Vat
```

#### MKR Token

```act
behaviour gem of Flopper
interface gem()

for all

    Gem : address

storage

    gem |-> Gem

iff

    VCallValue == 0

returns Gem
```

#### minimum bid increment

```act
behaviour beg of Flopper
interface beg()

for all

    Beg : uint256

storage

    beg |-> Beg

iff

    VCallValue == 0

returns Beg
```

#### auction time-to-live

```act
behaviour ttl of Flopper
interface ttl()

for all

    Ttl : uint48
    Tau : uint48

storage

    ttl_tau |-> #WordPackUInt48UInt48(Ttl, Tau)

iff

    VCallValue == 0

returns Ttl
```

#### maximum auction duration

```act
behaviour tau of Flopper
interface tau()

for all

    Ttl : uint48
    Tau : uint48

storage

    ttl_tau |-> #WordPackUInt48UInt48(Ttl, Tau)

iff

    VCallValue == 0

returns Tau
```

#### kick counter

```act
behaviour kicks of Flopper
interface kicks()

for all

    Kicks : uint256

storage

    kicks |-> Kicks

iff

    VCallValue == 0

returns Kicks
```

#### liveness flag

```act
behaviour live of Flopper
interface live()

for all

    Live : uint256

storage

    live |-> Live

iff

    VCallValue == 0

returns Live
```

### Mutators

#### Auth

Any owner can add and remove owners.

```act
behaviour rely-diff of Flopper
interface rely(address usr)

for all

    May : uint256

storage

    wards[CALLER_ID] |-> May
    wards[usr]       |-> _ => 1

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0

if

    CALLER_ID =/= usr
```

```act
behaviour rely-same of Flopper
interface rely(address usr)

for all

    May : uint256

storage

    wards[CALLER_ID] |-> May => 1

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0

if
    usr == CALLER_ID
```

```act
behaviour deny-diff of Flopper
interface deny(address usr)

for all

    May : uint256

storage

    wards[CALLER_ID] |-> May
    wards[usr]       |-> _ => 0

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0

if

    CALLER_ID =/= usr
```

```act
behaviour deny-same of Flopper
interface deny(address usr)

for all

    May : uint256

storage

    wards[CALLER_ID] |-> May => 0

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0

if

    CALLER_ID == usr
```

```act
behaviour addu48u48 of Flopper
interface add(uint48 x, uint48 y) internal

stack

    y : x : JMPTO : WS => JMPTO : x + y : WS

iff in range uint48

    x + y

if

    #sizeWordStack(WS) <= 100
```

```act
behaviour muluu of Flopper
interface mul(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : x * y : WS

iff in range uint256

    x * y

if

    // TODO: strengthen
    #sizeWordStack(WS) <= 1000
```

#### Auction parameters

```act
behaviour file of Flopper
interface file(bytes32 what, uint256 data)

for all

    May : uint256
    Beg : uint256
    Ttl : uint48
    Tau : uint48

storage

    wards[CALLER_ID] |-> May
    beg |-> Beg => (#if what == #string2Word("beg") #then data #else Beg #fi)
    ttl_tau |-> #WordPackUInt48UInt48(Ttl, Tau) => (#if what == #string2Word("ttl") #then #WordPackUInt48UInt48(data, Tau) #else (#if what == #string2Word("tau") #then #WordPackUInt48UInt48(Ttl, data) #else #WordPackUInt48UInt48(Ttl, Tau) #fi) #fi)

iff

    May == 1
    VCallValue == 0

if

    (what =/= #string2Word("ttl") and what =/= #string2Word("tau")) or #rangeUInt(48, data)
```

#### starting an auction

```act
behaviour kick of Flopper
interface kick(address gal, uint256 lot, uint256 bid)

for all
  Live     : uint256
  Kicks    : uint256
  Ttl      : uint48
  Tau      : uint48
  Old_lot  : uint256
  Old_bid  : uint256
  Old_guy  : address
  Old_tic  : uint48
  Old_end  : uint48
  Ward     : uint256

storage
  wards[CALLER_ID]            |-> Ward
  live                        |-> Live
  kicks                       |-> Kicks => 1 + Kicks
  ttl_tau                     |-> #WordPackUInt48UInt48(Ttl, Tau)
  bids[1 + Kicks].bid         |-> Old_bid => bid
  bids[1 + Kicks].lot         |-> Old_lot => lot
  bids[1 + Kicks].guy_tic_end |-> #WordPackAddrUInt48UInt48(Old_guy, Old_tic, Old_end) => #WordPackAddrUInt48UInt48(gal, Old_tic, TIME + Tau)

iff
  Ward == 1
  Live == 1
  VCallValue == 0

iff in range uint256
  Kicks + 1

iff in range uint48
  TIME + Tau

if
  #rangeUInt(48, TIME)

returns 1 + Kicks

calls
  Flapper.addu48u48
```

```act
behaviour dent of Flopper
interface dent(uint id, uint lot, uint bid)

for all
  Live : uint256
  Vat  : address VatLike
  Beg  : uint256
  Ttl  : uint48
  Tau  : uint48
  Bid  : uint256
  Lot  : uint256
  Guy  : address
  Tic  : uint48
  End  : uint48
  CanMove : uint256
  Dai_a   : uint256
  Dai_g   : uint256

storage
  live |-> Live
  vat  |-> Vat
  beg  |-> Beg
  ttl_tau |-> #WordPackUInt48UInt48(Ttl, Tau)
  bids[id].bid         |-> Bid
  bids[id].lot         |-> Lot => lot
  bids[id].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => #WordPackAddrUInt48UInt48(CALLER_ID, TIME + Ttl, End)

storage Vat
  can[CALLER_ID][ACCT_ID] |-> CanMove
  dai[CALLER_ID] |-> Dai_a => Dai_a - bid
  dai[Guy]       |-> Dai_g => Dai_g + bid

iff
  Live == 1
  Guy =/= 0
  Tic > TIME or Tic == 0
  End > TIME
  bid == Bid
  lot <  Lot
  (Beg * lot) / #Ray <= Lot
  CanMove == 1
  VCallValue == 0
  VCallDepth < 1024

iff in range uint256
  Dai_a - bid
  Dai_g + bid
  Beg * lot

iff in range uint48
  TIME + Ttl

if
  CALLER_ID =/= ACCT_ID
  CALLER_ID =/= Guy
  #rangeUInt(48, TIME)

calls
  Flopper.muluu
  Flopper.addu48u48
  Vat.move-diff
```

```act
behaviour deal of Flopper
interface deal(uint256 id)

for all
  Live    : uint256
  Bid     : uint256
  Lot     : uint256
  Guy     : address
  Tic     : uint48
  End     : uint48
  DSToken : address DSToken
  Gem_g   : uint256
  Stopped : bool
  Supply  : uint256
  Owner   : address

storage
  gem  |-> DSToken
  live |-> Live
  bids[id].bid         |-> Bid => 0
  bids[id].lot         |-> Lot => 0
  bids[id].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => 0

storage DSToken
  balances[Guy] |-> Gem_g  => Gem_g  + Lot
  supply        |-> Supply => Supply + Lot
  owner_stopped |-> #WordPackAddrUInt8(Owner, Stopped)

iff
  Live == 1
  Tic < TIME or End < TIME
  Tic =/= 0  or End < TIME
  Stopped == 0
  VCallValue == 0
  VCallDepth < 1024

iff in range uint256
  Gem_g  + Lot
  Supply + Lot

if
  Owner == ACCT_ID

calls
  DSToken.mint
```

```act
behaviour cage of Flopper
interface cage()

for all
  Ward : uint256
  Live : uint256

storage
  wards[CALLER_ID] |-> Ward
  live |-> Live => 0

iff
  Ward == 1
  VCallValue == 0
```

```act
behaviour yank of Flopper
interface yank(uint256 id)

for all
  Live   : uint256
  Vat    : address VatLike
  Bid    : uint256
  Lot    : uint256
  Guy    : address
  Tic    : uint48
  End    : uint48
  Dai_a  : uint256
  Dai_g  : uint256

storage
  live |-> Live
  vat  |-> Vat
  bids[id].bid |-> Bid => 0
  bids[id].lot |-> Lot => 0
  bids[id].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => 0

storage Vat
  can[ACCT_ID][ACCT_ID] |-> _
  dai[ACCT_ID] |-> Dai_a => Dai_a - Bid
  dai[Guy]     |-> Dai_g => Dai_g + Bid

iff
  Live == 0
  Guy =/= 0
  VCallDepth < 1024
  VCallValue == 0

if
  ACCT_ID =/= Guy

iff in range uint256
  Dai_a - Bid
  Dai_g + Bid

calls
  Vat.move-diff
```
