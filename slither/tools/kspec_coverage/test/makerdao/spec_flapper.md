```act
behaviour wards of Flapper
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
behaviour bids of Flapper
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
behaviour vat of Flapper
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
behaviour gem of Flapper
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
behaviour beg of Flapper
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
behaviour ttl of Flapper
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
behaviour tau of Flapper
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
behaviour kicks of Flapper
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
behaviour live of Flapper
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
behaviour rely-diff of Flapper
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
behaviour rely-same of Flapper
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
behaviour deny-diff of Flapper
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
behaviour deny-same of Flapper
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

#### Auction parameters

```act
behaviour file of Flapper
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
behaviour addu48u48 of Flapper
interface add(uint48 x, uint48 y) internal

stack

    y : x : JMPTO : WS => JMPTO : x + y : WS

iff in range uint48

    x + y

if

    #sizeWordStack(WS) <= 100
```

```act
behaviour muluu of Flapper
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
behaviour kick of Flapper
interface kick(uint256 lot, uint256 bid)

for all

    Vat      : address VatLike
    Kicks    : uint256
    Ttl      : uint48
    Tau      : uint48
    Bid      : uint256
    Lot      : uint256
    Old_guy  : address
    Old_tic  : uint48
    Old_end  : uint48
    CanMove  : uint256
    Dai_v    : uint256
    Dai_c    : uint256
    Live     : uint256

storage

    vat                         |-> Vat
    ttl_tau                     |-> #WordPackUInt48UInt48(Ttl, Tau)
    kicks                       |-> Kicks => 1 + Kicks
    bids[1 + Kicks].bid         |-> Bid => bid
    bids[1 + Kicks].lot         |-> Lot => lot
    bids[1 + Kicks].guy_tic_end |-> #WordPackAddrUInt48UInt48(Old_guy, Old_tic, Old_end) => #WordPackAddrUInt48UInt48(CALLER_ID, Old_tic, TIME + Tau)
    live                        |-> Live

storage Vat

    can[CALLER_ID][ACCT_ID] |-> CanMove
    dai[ACCT_ID]   |-> Dai_v => Dai_v + lot
    dai[CALLER_ID] |-> Dai_c => Dai_c - lot

iff

    Live == 1
    CanMove == 1
    VCallValue == 0
    VCallDepth < 1024

iff in range uint256

    Kicks + 1
    Dai_v + lot
    Dai_c - lot

iff in range uint48

    TIME + Tau

if

    CALLER_ID =/= ACCT_ID
    #rangeUInt(48, TIME)

returns 1 + Kicks

calls

    Vat.move-diff
    Flapper.addu48u48
```

#### Bidding on an auction (tend phase)

```act
behaviour tend of Flapper
interface tend(uint256 id, uint256 lot, uint256 bid)

for all

    DSToken : address DSToken
    Live    : uint256
    Ttl     : uint48
    Tau     : uint48
    Beg     : uint256
    Bid     : uint256
    Lot     : uint256
    Guy     : address
    Tic     : uint48
    End     : uint48
    Allowed : uint256
    Gem_g   : uint256
    Gem_a   : uint256
    Gem_u   : uint256
    Owner   : address
    Stopped : bool

storage

    gem                  |-> DSToken
    live                 |-> Live
    ttl_tau              |-> #WordPackUInt48UInt48(Ttl, Tau)
    beg                  |-> Beg
    bids[id].bid         |-> Bid => bid
    bids[id].lot         |-> Lot
    bids[id].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => #WordPackAddrUInt48UInt48(CALLER_ID, TIME + Ttl, End)

storage DSToken

    allowance[CALLER_ID][ACCT_ID] |-> Allowed => #if (Allowed == maxUInt256) #then Allowed #else Allowed - bid #fi
    balances[CALLER_ID] |-> Gem_u => Gem_u - bid
    balances[Guy]       |-> Gem_g => Gem_g + Bid
    balances[ACCT_ID]   |-> Gem_a => Gem_a + (bid - Bid)
    owner_stopped       |-> #WordPackAddrUInt8(Owner, Stopped)

iff
    VCallValue == 0
    VCallDepth < 1024
    Guy =/= 0
    Stopped == 0
    (Allowed == maxUInt256) or (bid <= Allowed)
    Live == 1
    Tic > TIME or Tic == 0
    End > TIME
    TIME + Ttl <= maxUInt48
    lot == Lot
    bid > Bid
    bid * #Ray <= maxUInt256
    bid * #Ray >= Beg * Bid

iff in range uint256
    Gem_u - bid
    Gem_g + Bid
    Gem_a + (bid - Bid)

if
    #rangeUInt(48, TIME)
    CALLER_ID =/= ACCT_ID
    CALLER_ID =/= Guy
    ACCT_ID   =/= Guy

calls
    Flapper.addu48u48
    Flapper.muluu
    DSToken.move
```

```act
behaviour deal of Flapper
interface deal(uint256 id)

for all
  DSToken : address DSToken
  Vat     : address VatLike
  Live    : uint256
  Bid     : uint256
  Lot     : uint256
  Guy     : address
  Tic     : uint48
  End     : uint48
  Dai_a   : uint256
  Dai_g   : uint256
  Gem_a   : uint256
  Supply  : uint256
  Owner   : address
  Stopped : bool

storage
  vat                  |-> Vat
  gem                  |-> DSToken
  live                 |-> Live
  bids[id].bid         |-> Bid => 0
  bids[id].lot         |-> Lot => 0
  bids[id].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => 0

storage Vat
  can[ACCT_ID][ACCT_ID] |-> _
  dai[ACCT_ID] |-> Dai_a => Dai_a - Lot
  dai[Guy]     |-> Dai_g => Dai_g + Lot

storage DSToken
  allowance[ACCT_ID][ACCT_ID] |-> _
  owner_stopped       |-> #WordPackAddrUInt8(Owner, Stopped)
  balances[ACCT_ID]   |-> Gem_a  => Gem_a  - Bid
  supply              |-> Supply => Supply - Bid

iff
  VCallValue == 0
  VCallDepth < 1024
  Live == 1
  Stopped == 0
  (Tic < TIME and Tic =/= 0) or (End < TIME)

if
  ACCT_ID == Owner
  ACCT_ID =/= Guy

iff in range uint256
  Dai_a  - Lot
  Dai_g  + Lot
  Gem_a  - Bid
  Supply - Bid

calls
  Vat.move-diff
  DSToken.burn-self
```

```act
behaviour cage of Flapper
interface cage(uint256 rad)

for all
  Vat   : address VatLike
  Ward  : uint256
  Live  : uint256
  Dai_a : uint256
  Dai_u : uint256

storage
  wards[CALLER_ID] |-> Ward
  vat              |-> Vat
  live             |-> Live => 0

iff
  Ward == 1
  VCallDepth < 1024
  VCallValue == 0

if
  CALLER_ID =/= ACCT_ID

storage Vat
  can[ACCT_ID][ACCT_ID] |-> _
  dai[ACCT_ID]   |-> Dai_a => Dai_a - rad
  dai[CALLER_ID] |-> Dai_u => Dai_u + rad

iff in range uint256
  Dai_a - rad
  Dai_u + rad

calls
  Vat.move-diff
```

```act
behaviour yank of Flapper
interface yank(uint256 id)

for all
  Live    : uint256
  DSToken : address DSToken
  Bid     : uint256
  Lot     : uint256
  Guy     : address
  Tic     : uint48
  End     : uint48
  Gem_a   : uint256
  Gem_g   : uint256
  Stopped : bool
  Owner   : address

storage
  live |-> Live
  gem  |-> DSToken
  bids[id].bid         |-> Bid => 0
  bids[id].lot         |-> Lot => 0
  bids[id].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => 0

storage DSToken
  balances[ACCT_ID] |-> Gem_a => Gem_a - Bid
  balances[Guy]     |-> Gem_g => Gem_g + Bid
  owner_stopped     |-> #WordPackAddrUInt8(Owner, Stopped)

iff
  Live == 0
  Guy =/= 0
  Stopped == 0
  VCallDepth < 1024
  VCallValue == 0

iff in range uint256
  Gem_a - Bid
  Gem_g + Bid

calls
  DSToken.move

if
  ACCT_ID =/= Guy
```
