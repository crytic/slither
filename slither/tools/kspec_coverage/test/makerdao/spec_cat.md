```act
behaviour wards of Cat
interface wards(address usr)

for all

    May : uint256

storage

    wards[usr] |-> May

iff

    VCallValue == 0

returns May
```

#### `ilk` data

```act
behaviour ilks of Cat
interface ilks(bytes32 ilk)

for all

    Chop : uint256
    Flip : address
    Lump : uint256

storage

    ilks[ilk].flip |-> Flip
    ilks[ilk].chop |-> Chop
    ilks[ilk].lump |-> Lump

iff

    VCallValue == 0

returns Flip : Chop : Lump
```

#### liveness

```act
behaviour live of Cat
interface live()

for all

    Live : uint256

storage

    live |-> Live

iff

    VCallValue == 0

returns Live
```

#### `vat` address

```act
behaviour vat of Cat
interface vat()

for all

    Vat : address

storage

    vat |-> Vat

iff

    VCallValue == 0

returns Vat
```

#### `vow` address

```act
behaviour vow of Cat
interface vow()

for all

    Vow : address

storage

    vow |-> Vow

iff

    VCallValue == 0

returns Vow
```

### Mutators

#### adding and removing owners

```act
behaviour rely-diff of Cat
interface rely(address usr)

for all

    May   : uint256

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
behaviour rely-same of Cat
interface rely(address usr)

for all

    May   : uint256

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
behaviour deny-diff of Cat
interface deny(address usr)

for all

    May   : uint256

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
behaviour deny-same of Cat
interface deny(address usr)

for all

    Could : uint256

storage

    wards[CALLER_ID] |-> Could => 0

iff

    // act: caller is `. ? : not` authorised
    Could == 1
    VCallValue == 0

if

    CALLER_ID == usr
```

#### setting contract addresses

```act
behaviour file-addr of Cat
interface file(bytes32 what, address data)

for all

    May : uint256
    Vow : address

storage

    wards[CALLER_ID] |-> May
    vow              |-> Vow => (#if what == #string2Word("vow") #then data #else Vow #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0
```

#### setting liquidation auction

```act
behaviour file-flip of Cat
interface file(bytes32 ilk, bytes32 what, address data)

for all

    Vat  : address VatLike
    May  : uint256
    Flip : address
    Can  : uint256

storage

    vat              |-> Vat
    wards[CALLER_ID] |-> May
    ilks[ilk].flip   |-> Flip => (#if what == #string2Word("flip") #then data #else Flip #fi)

storage Vat

    can[ACCT_ID][data] |-> Can => (#if what == #string2Word("flip") #then 1 #else Can #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0
    what =/= #string2Word("flip") or VCallDepth < 1024

calls
  Vat.hope
```

#### setting liquidation data

```act
behaviour file of Cat
interface file(bytes32 ilk, bytes32 what, uint256 data)

for all

    May  : uint256
    Chop : uint256
    Lump : uint256

storage

    wards[CALLER_ID] |-> May
    ilks[ilk].chop   |-> Chop => (#if what == #string2Word("chop") #then data #else Chop #fi)
    ilks[ilk].lump   |-> Lump => (#if what == #string2Word("lump") #then data #else Lump #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0
```

#### setting liquidator address

```
behaviour file-flip of Cat
interface file(bytes32 ilk, bytes32 what, address data)

for all

    Vat  : address VatLike
    May  : uint256
    Flip : address
    Hope : uint256

storage

    vat |-> Vat
    wards[CALLER_ID] |-> May
    ilks[ilk].flip   |-> Flip => (#if what == #string2Word("flip") #then data #else Flip #fi)

storage Vat

    can[ACCT_ID][data] |-> Hope => (#if what == #string2Word("flip") #then 1 #else Hope #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0

calls

  Vat.hope
```

#### liquidating a position

```act
behaviour muluu of Cat
interface mul(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : x * y : WS

iff in range uint256

    x * y

if

    #sizeWordStack(WS) <= 1000
```

```act
behaviour minuu of Cat
interface min(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : #if x > y #then y #else x #fi : WS

if

    #sizeWordStack(WS) <= 1000
```

```act
behaviour bite-full of Cat
interface bite(bytes32 ilk, address urn)

for all

    Vat     : address VatLike
    Vow     : address VowLike
    Flipper : address Flipper
    Live    : uint256
    Art_i   : uint256
    Rate_i  : uint256
    Spot_i  : uint256
    Line_i  : uint256
    Dust_i  : uint256
    Ink_iu  : uint256
    Art_iu  : uint256
    Gem_iv  : uint256
    Sin_w   : uint256
    Vice    : uint256
    Sin     : uint256
    Sin_era : uint256
    Chop    : uint256
    Lump    : uint256
    Kicks   : uint256
    Ttl     : uint48
    Tau     : uint48
    Bid     : uint256
    Lot     : uint256
    Guy     : address
    Tic     : uint48
    End     : uint48
    Gal     : address
    Tab     : uint256
    Usr     : address

storage

    vat            |-> Vat
    vow            |-> Vow
    live           |-> Live
    ilks[ilk].flip |-> Flipper
    ilks[ilk].chop |-> Chop
    ilks[ilk].lump |-> Lump

storage Vat
    ilks[ilk].Art      |-> Art_i => Art_i - Art_iu
    ilks[ilk].rate     |-> Rate_i
    ilks[ilk].spot     |-> Spot_i
    ilks[ilk].line     |-> Line_i
    ilks[ilk].dust     |-> Dust_i

    wards[ACCT_ID]     |-> CatMayVat
    urns[ilk][urn].ink |-> Ink_iu => 0
    urns[ilk][urn].art |-> Art_iu => 0
    gem[ilk][Flipper]  |-> Gem_iv => Gem_iv + Ink_iu
    sin[Vow]           |-> Sin_w  => Sin_w  + (Rate_i * Art_iu)
    vice               |-> Vice   => Vice   + (Rate_i * Art_iu)

storage Vow

    wards[ACCT_ID]     |-> CatMayVow
    sin[TIME]          |-> Sin_era => Sin_era + Rate_i * Art_iu
    Sin                |-> Sin     => Sin     + Rate_i * Art_iu

storage Flipper

    ttl_tau                     |-> #WordPackUInt48UInt48(Ttl, Tau)
    kicks                       |-> Kicks => 1 + Kicks
    bids[1 + Kicks].bid         |-> Bid => 0
    bids[1 + Kicks].lot         |-> Lot => Ink_iu
    bids[1 + Kicks].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => #WordPackAddrUInt48UInt48(ACCT_ID, Tic, TIME + Tau)
    bids[1 + Kicks].usr         |-> Usr => urn
    bids[1 + Kicks].gal         |-> Gal => Vow
    bids[1 + Kicks].tab         |-> Tab => (Chop * (Rate_i * Art_iu)) / #Ray


iff

    VCallValue == 0
    VCallDepth < 1023
    CatMayVat == 1
    CatMayVow == 1
    Live == 1
    Ink_iu * Spot_i < Art_iu * Rate_i
    Art_iu <= posMinSInt256
    Ink_iu <= posMinSInt256
    Ink_iu =/= 0

iff in range int256

    Rate_i
    Rate_i * Art_iu

iff in range uint256

    Art_i  - Art_iu
    Gem_iv + Ink_iu
    Sin_w   + Rate_i * Art_iu
    Vice    + Rate_i * Art_iu
    Sin_era + Rate_i * Art_iu
    Sin     + Rate_i * Art_iu
    Chop * (Rate_i * Art_iu)
    Lump * Art_iu
    Ink_iu * Art_iu

if

    Ink_iu < Lump


returns 1 + Kicks

calls

  Cat.muluu
  Cat.minuu
  Vat.grab
  Vat.ilks
  Vat.urns
  Vow.fess
  Flipper.kick
```

```act
behaviour bite-lump of Cat
interface bite(bytes32 ilk, address urn)

for all

    Vat     : address VatLike
    Vow     : address VowLike
    Flipper : address Flipper
    Live    : uint256
    Art_i   : uint256
    Rate_i  : uint256
    Spot_i  : uint256
    Line_i  : uint256
    Dust_i  : uint256
    Ink_iu  : uint256
    Art_iu  : uint256
    Gem_iv  : uint256
    Sin_w   : uint256
    Vice    : uint256
    Sin     : uint256
    Sin_era : uint256
    Chop    : uint256
    Lump    : uint256
    Kicks   : uint256
    Ttl     : uint48
    Tau     : uint48
    Bid     : uint256
    Lot     : uint256
    Guy     : address
    Tic     : uint48
    End     : uint48
    Gal     : address
    Tab     : uint256
    Usr     : address

storage

    vat            |-> Vat
    vow            |-> Vow
    live           |-> Live
    ilks[ilk].flip |-> Flipper
    ilks[ilk].chop |-> Chop
    ilks[ilk].lump |-> Lump

storage Vat

    ilks[ilk].Art      |-> Art_i  => Art_i - ((Lump * Art_iu) / Ink_iu)
    ilks[ilk].rate     |-> Rate_i
    ilks[ilk].spot     |-> Spot_i
    ilks[ilk].line     |-> Line_i
    ilks[ilk].dust     |-> Dust_i

    wards[ACCT_ID]     |-> CatMayVat
    urns[ilk][urn].ink |-> Ink_iu => Ink_iu - Lump
    urns[ilk][urn].art |-> Art_iu => Art_iu - ((Lump * Art_iu) / Ink_iu)
    gem[ilk][Flipper]  |-> Gem_iv => Gem_iv + Lump
    sin[Vow]           |-> Sin_w  => Sin_w  + Rate_i * ((Lump * Art_iu) / Ink_iu)
    vice               |-> Vice   => Vice   + Rate_i * ((Lump * Art_iu) / Ink_iu)

storage Vow

    wards[ACCT_ID]     |-> CatMayVow
    sin[TIME]          |-> Sin_era => Sin_era + Rate_i * ((Lump * Art_iu) / Ink_iu)
    Sin                |-> Sin     => Sin     + Rate_i * ((Lump * Art_iu) / Ink_iu)

storage Flipper

    ttl_tau                     |-> #WordPackUInt48UInt48(Ttl, Tau)
    kicks                       |-> Kicks => 1 + Kicks
    bids[1 + Kicks].bid         |-> Bid => 0
    bids[1 + Kicks].lot         |-> Lot => Lump
    bids[1 + Kicks].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => #WordPackAddrUInt48UInt48(ACCT_ID, Tic, TIME + Tau)
    bids[1 + Kicks].usr         |-> Usr => urn
    bids[1 + Kicks].gal         |-> Gal => Vow
    bids[1 + Kicks].tab         |-> Tab => (Chop * (Rate_i * ((Lump * Art_iu) / Ink_iu)) / #Ray)


iff

    VCallValue == 0
    VCallDepth < 1023
    CatMayVat == 1
    CatMayVow == 1
    Live == 1
    Ink_iu * Spot_i < Art_iu * Rate_i
    (Lump * Art_iu) / Ink_iu <= posMinSInt256
    Lump <= posMinSInt256
    Ink_iu =/= 0

iff in range int256

    Rate_i
    Rate_i * ((Lump * Art_iu) / Ink_iu)

iff in range uint256

    Rate_i * Art_iu
    Lump * Art_iu
    Ink_iu * Art_iu
    Art_i - ((Lump * Art_iu) / Ink_iu)
    Ink_iu - Lump
    Art_iu - ((Lump * Art_iu) / Ink_iu)
    Gem_iv + Lump
    Sin_w   + Rate_i * ((Lump * Art_iu) / Ink_iu)
    Vice    + Rate_i * ((Lump * Art_iu) / Ink_iu)
    Sin_era + Rate_i * ((Lump * Art_iu) / Ink_iu)
    Sin     + Rate_i * ((Lump * Art_iu) / Ink_iu)
    Chop * (Rate_i * ((Lump * Art_iu) / Ink_iu))

if

    Ink_iu >= Lump

returns 1 + Kicks

calls

  Cat.muluu
  Cat.minuu
  Vat.grab
  Vat.ilks
  Vat.urns
  Vow.fess
  Flipper.kick
```

```act
behaviour cage of Cat
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
