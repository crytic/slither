```act
behaviour wards of Flipper
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
behaviour bids of Flipper
interface bids(uint256 n)

for all

    Bid : uint256
    Lot : uint256
    Guy : address
    Tic : uint48
    End : uint48
    Usr : address
    Gal : address
    Tab : uint256

storage

    bids[n].bid         |-> Bid
    bids[n].lot         |-> Lot
    bids[n].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End)
    bids[n].usr         |-> Usr
    bids[n].gal         |-> Gal
    bids[n].tab         |-> Tab

iff

    VCallValue == 0

returns Bid : Lot : Guy : Tic : End : Usr : Gal : Tab
```

#### cdp engine

```act
behaviour vat of Flipper
interface vat()

for all

    Vat : address

storage

    vat |-> Vat

iff

    VCallValue == 0

returns Vat
```

#### collateral type

```act
behaviour ilk of Flipper
interface ilk()

for all

    Ilk : uint256

storage

    ilk |-> Ilk

iff

    VCallValue == 0

returns Ilk
```

#### minimum bid increment

```act
behaviour beg of Flipper
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
behaviour ttl of Flipper
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
behaviour tau of Flipper
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
behaviour kicks of Flipper
interface kicks()

for all

    Kicks : uint256

storage

    kicks |-> Kicks

iff

    VCallValue == 0

returns Kicks
```

### Mutators

#### Auth

Any owner can add and remove owners.

```act
behaviour rely-diff of Flipper
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
behaviour rely-same of Flipper
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
behaviour deny-diff of Flipper
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
behaviour deny-same of Flipper
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
behaviour file of Flipper
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

```act
behaviour addu48u48 of Flipper
interface add(uint48 x, uint48 y) internal

stack

    y : x : JMPTO : WS => JMPTO : x + y : WS

iff in range uint48

    x + y

if

    #sizeWordStack(WS) <= 100
```

```act
behaviour muluu of Flipper
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
behaviour kick of Flipper
interface kick(address usr, address gal, uint256 tab, uint256 lot, uint256 bid)

for all

    Vat      : address VatLike
    Ilk      : uint256
    Kicks    : uint256
    Ttl      : uint48
    Tau      : uint48
    Bid      : uint256
    Lot      : uint256
    Guy      : address
    Tic      : uint48
    End      : uint48
    Usr      : address
    Gal      : address
    Tab      : uint256
    CanFlux  : uint256
    Gem_v    : uint256
    Gem_c    : uint256

storage

    vat                         |-> Vat
    ilk                         |-> Ilk
    ttl_tau                     |-> #WordPackUInt48UInt48(Ttl, Tau)
    kicks                       |-> Kicks => 1 + Kicks
    bids[1 + Kicks].bid         |-> Bid => bid
    bids[1 + Kicks].lot         |-> Lot => lot
    bids[1 + Kicks].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => #WordPackAddrUInt48UInt48(CALLER_ID, Tic, TIME + Tau)
    bids[1 + Kicks].usr         |-> Usr => usr
    bids[1 + Kicks].gal         |-> Gal => gal
    bids[1 + Kicks].tab         |-> Tab => tab

storage Vat

    can[CALLER_ID][ACCT_ID] |-> CanFlux
    gem[Ilk][CALLER_ID]     |-> Gem_v => Gem_v - lot
    gem[Ilk][ACCT_ID]       |-> Gem_c => Gem_c + lot

iff

    CanFlux == 1
    VCallDepth < 1024
    VCallValue == 0

iff in range uint256

    Kicks + 1
    Gem_v - lot
    Gem_c + lot

iff in range uint48

    TIME + Tau

if

    CALLER_ID =/= ACCT_ID
    #rangeUInt(48, TIME)

calls

  Flipper.addu48u48
  Vat.flux-diff

returns 1 + Kicks
```

```act
behaviour tick of Flipper
interface tick(uint256 id)

for all
  Tau : uint48
  Ttl : uint48
  Guy : address
  Tic : uint48
  End : uint48

storage
  ttl_tau              |-> #WordPackUInt48UInt48(Ttl, Tau)
  bids[id].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => #WordPackAddrUInt48UInt48(Guy, Tic, TIME + Tau)

iff
  End < TIME
  Tic == 0
  VCallValue == 0

iff in range uint48
  TIME + Tau

if
  #rangeUInt(48, TIME)

calls
  Flipper.addu48u48
```

```act
behaviour tend of Flipper
interface tend(uint256 id, uint256 lot, uint256 bid)

for all
  Vat : address VatLike
  Beg : uint256
  Bid : uint256
  Lot : uint256
  Tab : uint256
  Gal : address
  Ttl : uint48
  Tau : uint48
  Guy : address
  Tic : uint48
  End : uint48
  Can   : uint256
  Dai_c : uint256
  Dai_u : uint256
  Dai_g : uint256

storage
  vat          |-> Vat
  beg          |-> Beg
  ttl_tau      |-> #WordPackUInt48UInt48(Ttl, Tau)
  bids[id].bid |-> Bid => bid
  bids[id].lot |-> Lot => lot
  bids[id].tab |-> Tab
  bids[id].gal |-> Gal
  bids[id].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => #WordPackAddrUInt48UInt48(CALLER_ID, TIME + Ttl, End)

storage Vat
  can[CALLER_ID][ACCT_ID] |-> Can
  dai[CALLER_ID] |-> Dai_c => Dai_c - bid
  dai[Guy]       |-> Dai_u => Dai_u + Bid
  dai[Gal]       |-> Dai_g => Dai_g + (bid - Bid)

iff
  VCallValue == 0
  VCallDepth < 1024
  Guy =/= 0
  Can == 1
  Tic > TIME or Tic == 0
  End > TIME
  TIME + Ttl <= maxUInt48
  lot == Lot
  bid >  Bid
  bid <= Dai_c
  Dai_u + Bid <= maxUInt256
  Dai_g + (bid - Bid) <= maxUInt256
  bid * #Ray <= maxUInt256
  ((bid < Tab) and (bid * #Ray >= Beg * Bid)) or ((bid == Tab) and (Beg * Bid <= maxUInt256))

if
  CALLER_ID =/= ACCT_ID
  CALLER_ID =/= Guy
  CALLER_ID =/= Gal
  Guy =/= Gal

calls
  Flipper.addu48u48
  Flipper.muluu
  Vat.move-diff
```

```act
behaviour dent of Flipper
interface dent(uint256 id, uint256 lot, uint256 bid)

for all
  Vat : address VatLike
  Ilk : bytes32
  Ttl : uint48
  Tau : uint48
  Beg : uint256
  Bid : uint256
  Lot : uint256
  Guy : address
  Tic : uint48
  End : uint48
  Gal : address
  Usr : address
  Tab : uint256
  Dai_c : uint256
  Dai_g : uint256
  Gem_a : uint256
  Gem_u : uint256

storage
  vat          |-> Vat
  ilk          |-> Ilk
  beg          |-> Beg
  ttl_tau      |-> #WordPackUInt48UInt48(Ttl, Tau)
  bids[id].bid |-> Bid
  bids[id].lot |-> Lot => lot
  bids[id].tab |-> Tab
  bids[id].usr |-> Usr
  bids[id].gal |-> Gal
  bids[id].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => #WordPackAddrUInt48UInt48(CALLER_ID, TIME + Ttl, End)

storage Vat
  can[CALLER_ID][ACCT_ID] |-> Can
  can[ACCT_ID][ACCT_ID]   |-> _
  dai[CALLER_ID]    |-> Dai_c => Dai_c - bid
  dai[Guy]          |-> Dai_g => Dai_g + bid
  gem[Ilk][ACCT_ID] |-> Gem_a => Gem_a - (Lot - lot)
  gem[Ilk][Usr]     |-> Gem_u => Gem_u + (Lot - lot)

iff
  VCallValue == 0
  VCallDepth < 1024
  Guy =/= 0
  Can == 1
  Tic > TIME or Tic == 0
  End > TIME
  TIME + Ttl <= maxUInt48
  bid == Bid
  bid == Tab
  lot <  Lot
  Gem_u + (Lot - lot) <= maxUInt256
  Gem_a >= (Lot - lot)
  bid <= Dai_c
  Dai_g + bid <= maxUInt256
  Lot * #Ray >= lot * Beg
  Lot * #Ray <= maxUInt256

if
  #rangeUInt(48, TIME)
  CALLER_ID =/= ACCT_ID
  CALLER_ID =/= Guy
  ACCT_ID   =/= Usr

calls
  Flipper.muluu
  Vat.move-diff
  Vat.flux-diff
```

```act
behaviour deal of Flipper
interface deal(uint256 id)

for all
  Vat : address VatLike
  Ilk : bytes32
  Bid : uint256
  Lot : uint256
  Guy : address
  Tic : uint48
  End : uint48
  Tab : uint256
  Gem_a : uint256
  Gem_u : uint256
  Old_gal : address
  Old_usr : address

storage
  vat                  |-> Vat
  ilk                  |-> Ilk
  bids[id].bid         |-> Bid => 0
  bids[id].lot         |-> Lot => 0
  bids[id].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => 0
  bids[id].usr         |-> Old_usr => 0
  bids[id].gal         |-> Old_gal => 0
  bids[id].tab         |-> Tab => 0

storage Vat
  can[ACCT_ID][ACCT_ID] |-> _
  gem[Ilk][ACCT_ID] |-> Gem_a => Gem_a - Lot
  gem[Ilk][Guy]     |-> Gem_u => Gem_u + Lot

iff
  Tic =/= 0
  Tic < TIME or End < TIME
  VCallValue == 0
  VCallDepth < 1024

if
  ACCT_ID =/= Guy

iff in range uint256
  Gem_a - Lot
  Gem_u + Lot

calls
  Vat.flux-diff
```

```act
behaviour yank of Flipper
interface yank(uint256 id)

for all
  Vat : address VatLike
  Ttl : uint48
  Tau : uint48
  Ilk : bytes32
  Bid : uint256
  Lot : uint256
  Guy : address
  Tic : uint48
  End : uint48
  Usr : address
  Gal : address
  Tab : uint256
  Dai_c : uint256
  Dai_g : uint256
  Gem_a : uint256
  Gem_c : uint256

storage
  wards[CALLER_ID]     |-> May
  vat                  |-> Vat
  ilk                  |-> Ilk
  bids[id].bid         |-> Bid => 0
  bids[id].lot         |-> Lot => 0
  bids[id].tab         |-> Tab => 0
  bids[id].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => 0
  bids[id].usr         |-> Usr => 0
  bids[id].gal         |-> Gal => 0

storage Vat
  can[CALLER_ID][ACCT_ID] |-> Can
  can[ACCT_ID][ACCT_ID]   |-> _
  gem[Ilk][ACCT_ID]   |-> Gem_a => Gem_a - Lot
  gem[Ilk][CALLER_ID] |-> Gem_c => Gem_c + Lot
  dai[CALLER_ID]      |-> Dai_c => Dai_c - Bid
  dai[Guy]            |-> Dai_g => Dai_g + Bid

iff
  May == 1
  Guy =/= 0
  Can == 1
  Bid < Tab
  VCallValue == 0
  VCallDepth < 1024

if
  CALLER_ID =/= ACCT_ID
  CALLER_ID =/= Guy

iff in range uint256
  Gem_a - Lot
  Gem_c + Lot
  Dai_c - Bid
  Dai_g + Bid

calls
  Vat.flux-diff
  Vat.move-diff
```
