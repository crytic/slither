```act
behaviour rely-diff of End
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
behaviour rely-same of End
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
behaviour deny-diff of End
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
behaviour deny-same of End
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

### Math Lemmas

```act
behaviour adduu of End
interface add(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : x + y : WS

iff in range uint256

    x + y

if

    // TODO: strengthen
    #sizeWordStack(WS) <= 100
```

```act
behaviour subuu of End
interface sub(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : x - y : WS

iff in range uint256

    x - y

if

    // TODO: strengthen
    #sizeWordStack(WS) <= 100
```


```act
behaviour muluu of End
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
behaviour minuu of End
interface min(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : #if x <= y #then x #else y #fi : WS

if

    #sizeWordStack(WS) <= 1000
```

```act
behaviour rmul of End
interface rmul(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : (x * y) / #Ray : WS

iff in range uint256

    x * y

if

    // TODO: strengthen
    #sizeWordStack(WS) <= 1000
```

```act
behaviour rdiv of End
interface rdiv(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : (x * #Ray) / y : WS

iff

    y =/= 0

iff in range uint256

    x * #Ray

if

    // TODO: strengthen
    #sizeWordStack(WS) <= 1000
```


### Accessors

```act
behaviour wards of End
interface wards(address usr)

for all

    May : uint256

storage

    wards[usr] |-> May

iff

    VCallValue == 0

returns May
```

```act
behaviour vat of End
interface vat()

for all

    Vat : address

storage

    vat |-> Vat

iff

    VCallValue == 0

returns Vat
```

```act
behaviour cat of End
interface cat()

for all

    Cat : address

storage

    cat |-> Cat

iff

    VCallValue == 0

returns Cat
```

#### `vow` address

```act
behaviour vow of End
interface vow()

for all

    Vow : address

storage

    vow |-> Vow

iff

    VCallValue == 0

returns Vow
```


#### `spot` address

```act
behaviour spot of End
interface spot()

for all

    Spot : address

storage

    spot |-> Spot

iff

    VCallValue == 0

returns Spot
```

#### liveness

```act
behaviour live of End
interface live()

for all

    Live : uint256

storage

    live |-> Live

iff

    VCallValue == 0

returns Live
```

### Setting `End` parameters

```act
behaviour file-wait of End
interface file(bytes32 what, uint256 data)

for all

    May  : uint256
    Wait : uint256

storage

    wards[CALLER_ID] |-> May
    wait |-> Wait => (#if what == #string2Word("wait") #then data #else Wait #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0
```

```act
behaviour file-addr of End
interface file(bytes32 what, address data)

for all

    May  : uint256
    Vat  : address
    Cat  : address
    Vow  : address
    Spot : address

storage

    wards[CALLER_ID] |-> May
    vat  |-> Vat  => (#if what == #string2Word("vat")  #then data #else Vat #fi)
    cat  |-> Cat  => (#if what == #string2Word("cat")  #then data #else Cat #fi)
    vow  |-> Vow  => (#if what == #string2Word("vow")  #then data #else Vow #fi)
    spot |-> Spot => (#if what == #string2Word("spot") #then data #else Spot #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0
```

### Time of cage

```act
behaviour when of End
interface when()

for all

    When : uint256

storage

    when |-> When

iff

    VCallValue == 0

returns When
```

### Processing period

```act
behaviour wait of End
interface wait()

for all

    Wait : uint256

storage

    wait |-> Wait

iff

    VCallValue == 0

returns Wait
```

### Total Outstanding Debt

```act
behaviour debt of End
interface debt()

for all

    Debt : uint256

storage

    debt |-> Debt

iff

    VCallValue == 0

returns Debt
```

### Ilk Data

```act
behaviour tag of End
interface tag(bytes32 ilk)

for all

    Ray : uint256

storage

    tag[ilk] |-> Ray

iff

    VCallValue == 0

returns Ray
```

```act
behaviour gap of End
interface gap(bytes32 ilk)

for all

    Wad : uint256

storage

    gap[ilk] |-> Wad

iff

    VCallValue == 0

returns Wad
```

```act
behaviour Art of End
interface Art(bytes32 ilk)

for all

    Wad : uint256

storage

    Art[ilk] |-> Wad

iff

    VCallValue == 0

returns Wad
```

```act
behaviour fix of End
interface fix(bytes32 ilk)

for all

    Ray : uint256

storage

    fix[ilk] |-> Ray

iff

    VCallValue == 0

returns Ray
```

```act
behaviour bag of End
interface bag(address usr)

for all

    Wad : uint256

storage

    bag[usr] |-> Wad

iff

    VCallValue == 0

returns Wad
```

```act
behaviour out of End
interface out(bytes32 ilk, address usr)

for all

    Wad : uint256

storage

    out[ilk][usr] |-> Wad

iff

    VCallValue == 0

returns Wad
```

## Behaviours

```act
behaviour cage-surplus of End
interface cage()

for all

    Vat : address VatLike
    Cat : address Cat
    Vow : address VowLike
    Flapper : address Flapper
    Flopper : address Flopper
    FlapVat : address

    Live : uint256
    When : uint256

    VatLive  : uint256
    CatLive  : uint256
    VowLive  : uint256
    FlapLive : uint256
    FlopLive : uint256

    CallerMay : uint256
    EndMayVat : uint256
    EndMayCat : uint256
    EndMayVow : uint256
    VowMayFlap : uint256
    VowMayFlop : uint256

    Dai_f : uint256
    Awe   : uint256
    Joy   : uint256
    Sin   : uint256
    Ash   : uint256

storage

    live |-> Live => 0
    when |-> When => TIME
    vat |-> Vat
    cat |-> Cat
    vow |-> Vow
    wards[CALLER_ID] |-> CallerMay

storage Vat

    can[Flapper][Flapper] |-> _
    live |-> VatLive => 0
    wards[ACCT_ID] |-> EndMayVat
    dai[Flapper]   |-> Dai_f => 0
    sin[Vow]       |-> Awe   => 0
    dai[Vow]       |-> Joy   => (Joy + Dai_f) - Awe

storage Cat

    live |-> CatLive => 0
    wards[ACCT_ID] |-> EndMayCat

storage Vow

    live |-> VowLive => 0
    wards[ACCT_ID] |-> EndMayVow
    flapper |-> Flapper
    flopper |-> Flopper
    Sin |-> Sin => 0
    Ash |-> Ash => 0

storage Flapper

    wards[Vow] |-> VowMayFlap
    vat  |-> FlapVat
    live |-> FlapLive => 0

storage Flopper

    wards[Vow] |-> VowMayFlop
    live |-> FlopLive => 0

iff

    VCallValue == 0
    VCallDepth < 1022
    Live == 1
    CallerMay == 1
    EndMayVat == 1
    EndMayCat == 1
    EndMayVow == 1
    VowMayFlap == 1
    VowMayFlop == 1

if
    Joy + Dai_f > Awe
    FlapVat == Vat

calls

  Vat.cage
  Cat.cage
  Vow.cage-surplus
```

```act
behaviour cage-deficit of End
interface cage()

for all

    Vat : address VatLike
    Cat : address Cat
    Vow : address VowLike
    Flapper : address Flapper
    Flopper : address Flopper
    FlapVat : address

    Live : uint256
    When : uint256

    VatLive  : uint256
    CatLive  : uint256
    VowLive  : uint256
    FlapLive : uint256
    FlopLive : uint256

    CallerMay : uint256
    EndMayVat : uint256
    EndMayCat : uint256
    EndMayVow : uint256
    VowMayFlap : uint256
    VowMayFlop : uint256

    Dai_f : uint256
    Awe   : uint256
    Joy   : uint256
    Sin   : uint256
    Ash   : uint256

storage

    live |-> Live => 0
    when |-> When => TIME
    vat |-> Vat
    cat |-> Cat
    vow |-> Vow
    wards[CALLER_ID] |-> CallerMay

storage Vat

    live |-> VatLive => 0
    wards[ACCT_ID] |-> EndMayVat
    dai[Flap] |-> Dai_f => 0
    sin[Vow]  |-> Awe   => (Awe - Joy) - Dai_f
    dai[Vow]  |-> Joy   => 0

storage Cat

    live |-> CatLive => 0
    wards[ACCT_ID] |-> EndMayCat

storage Vow

    live |-> VowLive => 0
    wards[ACCT_ID] |-> EndMayVow
    flapper |-> Flapper
    flopper |-> Flopper
    Sin |-> Sin => 0
    Ash |-> Ash => 0

storage Flapper

    wards[Vow] |-> VowMayFlap
    vat  |-> FlapVat
    live |-> FlapLive => 0

storage Flopper

    wards[Vow] |-> VowMayFlop
    live |-> FlopLive => 0

iff

    VCallValue == 0
    VCallDepth < 1022
    Live == 1
    CallerMay == 1
    EndMayVat == 1
    EndMayCat == 1
    EndMayVow == 1
    VowMayFlap == 1
    VowMayFlop == 1

if
    Joy + Dai_f < Awe
    FlapVat == Vat

calls

  Vat.cage
  Cat.cage
  Vow.cage-deficit
```

```act
behaviour cage-balance of End
interface cage()

for all

    Vat : address VatLike
    Cat : address Cat
    Vow : address VowLike
    Flapper : address Flapper
    Flopper : address Flopper
    FlapVat : address

    Live : uint256
    When : uint256

    VatLive  : uint256
    CatLive  : uint256
    VowLive  : uint256
    FlapLive : uint256
    FlopLive : uint256

    CallerMay : uint256
    EndMayVat : uint256
    EndMayCat : uint256
    EndMayVow : uint256
    VowMayFlap : uint256
    VowMayFlop : uint256

    Dai_f : uint256
    Awe   : uint256
    Joy   : uint256
    Sin   : uint256
    Ash   : uint256

storage

    live |-> Live => 0
    when |-> When => TIME
    vat |-> Vat
    cat |-> Cat
    vow |-> Vow
    wards[CALLER_ID] |-> CallerMay

storage Vat

    can[Flapper][Flapper] |-> _
    live |-> VatLive => 0
    wards[ACCT_ID] |-> EndMayVat
    dai[Flapper]   |-> Dai_f => 0
    sin[Vow]       |-> Awe   => 0
    dai[Vow]       |-> Joy   => 0

storage Cat

    live |-> CatLive => 0
    wards[ACCT_ID] |-> EndMayCat

storage Vow

    live |-> VowLive => 0
    wards[ACCT_ID] |-> EndMayVow
    flapper |-> Flapper
    flopper |-> Flopper
    Sin |-> Sin => 0
    Ash |-> Ash => 0

storage Flapper

    wards[Vow] |-> VowMayFlap
    vat  |-> FlapVat
    live |-> FlapLive => 0

storage Flopper

    wards[Vow] |-> VowMayFlop
    live |-> FlopLive => 0

iff

    VCallValue == 0
    VCallDepth < 1022
    Live == 1
    CallerMay == 1
    EndMayVat == 1
    EndMayCat == 1
    EndMayVow == 1
    VowMayFlap == 1
    VowMayFlop == 1

if
    Joy + Dai_f == Awe
    FlapVat ==  Vat

calls

  Vat.cage
  Cat.cage
  Vow.cage-balance
```

```act
behaviour cage-ilk of End
interface cage(bytes32 ilk)

for all
  Live    : uint256
  Tag_i   : uint256
  Art_i   : uint256
  Rate_i  : uint256
  Spot_i  : uint256
  Line_i  : uint256
  Dust_i  : uint256
  Mat_i   : uint256
  Vat     : address VatLike
  Spotter : address Spotter
  DSValue : address DSValue
  Price   : uint256
  Owner   : address
  Ok      : bool

storage
  live     |-> Live
  vat      |-> Vat
  spot     |-> Spotter
  Art[ilk] |-> Art_i
  tag[ilk] |-> Tag_i => (#Wad * #Ray) / Price

storage Spotter
  ilks[ilk].pip |-> DSValue
  ilks[ilk].mat |-> Mat_i

storage Vat
  ilks[ilk].Art  |-> Art_i
  ilks[ilk].rate |-> Rate_i
  ilks[ilk].spot |-> Spot_i
  ilks[ilk].line |-> Line_i
  ilks[ilk].dust |-> Dust_i

storage DSValue
  1 |-> #WordPackAddrUInt8(Owner, Ok)
  2 |-> Price

iff
  VCallValue == 0
  VCallDepth < 1024
  Live == 0
  Tag_i == 0
  Ok == 1
  Price =/= 0

iff in range uint256
  #Wad * #Ray

calls
  End.rdiv
  Vat.ilks
  Spotter.ilks
  DSValue.read
```

```act
behaviour skip of End
interface skip(bytes32 ilk, uint256 id)

for all
  Vat        : address VatLike
  Cat        : address Cat
  Vow        : address
  Tag        : uint256
  Art        : uint256
  Flipper    : address Flipper
  Lump       : uint256
  Chop       : uint256
  EndMayYank : uint256
  Bid        : uint256
  Lot        : uint256
  Guy        : address
  Tic        : uint48
  End        : uint48
  Usr        : address
  Gal        : address
  Tab        : uint256
  EndMayVat  : uint256
  Art_i      : uint256
  Rate_i     : uint256
  Spot_i     : uint256
  Line_i     : uint256
  Dust_i     : uint256
  FlipCan    : uint256
  Dai_e      : uint256
  Dai_g      : uint256
  Joy        : uint256
  Debt       : uint256
  Awe        : uint256
  Vice       : uint256
  Gem_a      : uint256
  Gem_f      : uint256
  Ink_iu     : uint256
  Art_iu     : uint256

storage
  vat      |-> Vat
  cat      |-> Cat
  vow      |-> Vow
  tag[ilk] |-> Tag
  Art[ilk] |-> Art => Art + (Tab / Rate_i)

storage Cat
  ilks[ilk].flip |-> Flipper
  ilks[ilk].lump |-> Lump
  ilks[ilk].chop |-> Chop

storage Flipper
  wards[ACCT_ID]       |-> EndMayYank
  bids[id].bid         |-> Bid => 0
  bids[id].lot         |-> Lot => 0
  bids[id].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => 0
  bids[id].usr         |-> Usr => 0
  bids[id].gal         |-> Gal => 0
  bids[id].tab         |-> Tab => 0

storage Vat
  wards[ACCT_ID] |-> EndMayVat
  ilks[ilk].Art  |-> Art_i
  ilks[ilk].rate |-> Rate_i
  ilks[ilk].spot |-> Spot_i
  ilks[ilk].line |-> Line_i
  ilks[ilk].dust |-> Dust_i

  can[ACCT_ID][Flipper] |-> FlipCan => 1

  dai[ACCT_ID] |-> Dai_e
  dai[Guy] |-> Dai_g => Dai_g + Bid
  dai[Vow] |-> Joy   => (Joy  + Tab)
  debt     |-> Debt  => (Debt + Tab) + Bid
  sin[Vow] |-> Awe   => (Awe  + Bid)
  vice     |-> Vice  => (Vice + Bid)

  gem[ilk][ACCT_ID]  |-> Gem_a
  gem[ilk][Flipper]  |-> Gem_f  => Gem_f  - Lot
  urns[ilk][Urn].ink |-> Ink_iu => Ink_iu + Lot
  urns[ilk][Urn].art |-> Art_iu => Art_iu + (Tab / Rate_i)

iff
  VCallValue == 0
  VCallDepth < 1023
  Tag =/= 0
  EndMayVat == 1
  EndMayYank == 1
  Guy =/= 0
  Bid < Tab
  Lot <= posMinSInt256
  Tab / Rate_i <= posMinSInt256

iff in range uint256
  Joy + Tab
  (Awe  + Tab) + Bid
  (Vice + Tab) + Bid
  (Debt + Tab) + Bid
  Gem_f - Lot
  Gem_a + Lot
  Dai_e + Bid
  Dai_e - Bid
  Dai_g + Bid
  Art    + (Tab / Rate_i)
  Ink_iu + Lot
  Art_iu + (Tab / Rate_i)
  Art_i  + (Tab / Rate_i)

iff in range int256
  Rate_i
  Rate_i * (Tab / Rate_i)

if
  Flipper =/= ACCT_ID
  Flipper =/= Guy
  Guy =/= Vow
  Guy =/= ACCT_ID
  Vow =/= ACCT_ID

calls
  End.adduu
  Vat.ilks
  Vat.suck
  Vat.hope
  Vat.grab
  Cat.ilks
  Flipper.bids
  Flipper.yank
```

```act
behaviour skim of End
interface skim(bytes32 ilk, address urn)

for all
  Vat    : address VatLike
  Vow    : address
  Tag    : uint256
  Gap    : uint256
  Ward   : uint256
  Art_i  : uint256
  Rate_i : uint256
  Spot_i : uint256
  Line_i : uint256
  Dust_i : uint256
  Gem_a  : uint256
  Ink_iu : uint256
  Art_iu : uint256
  Awe    : uint256
  Vice   : uint256

storage
  vat      |-> Vat
  vow      |-> Vow
  tag[ilk] |-> Tag
  gap[ilk] |-> Gap

storage Vat
  wards[ACCT_ID]     |-> Ward
  ilks[ilk].Art      |-> Art_i => Art_i - Art_iu
  ilks[ilk].rate     |-> Rate_i
  ilks[ilk].spot     |-> Spot_i
  ilks[ilk].line     |-> Line_i
  ilks[ilk].dust     |-> Dust_i

  gem[ilk][ACCT_ID]  |-> Gem_a  => Gem_a  + ((((Rate_i * Art_iu) / #Ray) * Tag) / #Ray)
  urns[ilk][urn].ink |-> Ink_iu => Ink_iu - ((((Rate_i * Art_iu) / #Ray) * Tag) / #Ray)
  urns[ilk][urn].art |-> Art_iu => 0
  sin[Vow]           |-> Awe  => Awe  + (Rate_i * Art_iu)
  vice               |-> Vice => Vice + (Rate_i * Art_iu)

iff
  VCallValue == 0
  VCallDepth < 1024
  Tag =/= 0
  ((((Rate_i * Art_iu) / #Ray) * Tag) / #Ray) <= posMinSInt256
  Art_iu <= posMinSInt256
  Ward == 1

iff in range int256
  Rate_i
  Rate_i * Art_iu

iff in range uint256
  Art_i - Art_iu
  ((Rate_i * Art_iu) / #Ray) * Tag
  Gem_a  + ((((Rate_i * Art_iu) / #Ray) * Tag) / #Ray)
  Awe  + (Rate_i * Art_iu)
  Vice + (Rate_i * Art_iu)

if
  Ink_iu > ((((Rate_i * Art_iu) / #Ray) * Tag) / #Ray)

calls
  End.adduu
  End.subuu
  End.rmul
  End.minuu
  Vat.urns
  Vat.ilks
  Vat.grab
```

```act
behaviour bail of End
interface skim(bytes32 ilk, address urn)

for all
  Vat    : address VatLike
  Vow    : address
  Tag    : uint256
  Gap    : uint256
  Ward   : uint256
  Art_i  : uint256
  Rate_i : uint256
  Spot_i : uint256
  Line_i : uint256
  Dust_i : uint256
  Gem_a  : uint256
  Ink_iu : uint256
  Art_iu : uint256
  Awe    : uint256
  Vice   : uint256

storage
  vat      |-> Vat
  vow      |-> Vow
  tag[ilk] |-> Tag
  gap[ilk] |-> Gap => Gap + (((((Art_iu * Rate_i) / #Ray) * Tag) / #Ray) - Ink_iu)

storage Vat
  wards[ACCT_ID]     |-> Ward
  ilks[ilk].Art      |-> Art_i => Art_i - Art_iu
  ilks[ilk].rate     |-> Rate_i
  ilks[ilk].spot     |-> Spot_i
  ilks[ilk].line     |-> Line_i
  ilks[ilk].dust     |-> Dust_i

  gem[ilk][ACCT_ID]  |-> Gem_a  => Gem_a  + Ink_iu
  urns[ilk][urn].ink |-> Ink_iu => 0
  urns[ilk][urn].art |-> Art_iu => 0
  sin[Vow]           |-> Awe  => Awe  + (Rate_i * Art_iu)
  vice               |-> Vice => Vice + (Rate_i * Art_iu)

iff
  VCallValue == 0
  VCallDepth < 1024
  Tag =/= 0
  Ink_iu <= posMinSInt256
  Art_iu <= posMinSInt256
  Ward == 1

iff in range int256

  Rate_i
  Rate_i * Art_iu

iff in range uint256
  Gap + (((((Rate_i * Art_iu) / #Ray) * Tag) / #Ray) - Ink_iu)
  Art_i - Art_iu
  ((Rate_i * Art_iu) / #Ray) * Tag
  Gem_a + Ink_iu
  Awe  + (Rate_i * Art_iu)
  Vice + (Rate_i * Art_iu)

if

  Ink_iu <= ((((Rate_i * Art_iu) / #Ray) * Tag) / #Ray)

calls
  End.adduu
  End.subuu
  End.rmul
  End.minuu
  Vat.urns
  Vat.ilks
  Vat.grab
```

```act
behaviour thaw of End
interface thaw()

for all
  Vat  : address VatLike
  Vow  : address
  Live : uint256
  Debt : uint256
  When : uint256
  Wait : uint256
  Joy  : uint256
  FinalDebt : uint256

storage
  vat  |-> Vat
  vow  |-> Vow
  live |-> Live
  debt |-> Debt => FinalDebt
  when |-> When
  wait |-> Wait

storage Vat
  dai[Vow] |-> Joy
  debt     |-> FinalDebt

iff
  Live == 0
  Debt == 0
  Joy  == 0
  TIME >= When + Wait
  VCallValue == 0
  VCallDepth < 1024

calls
  End.adduu
  Vat.dai
  Vat.debt
```

```act
behaviour free of End
interface free(bytes32 ilk)

for all
  Vat    : address VatLike
  Vow    : address
  Ward   : uint256
  Live   : uint256
  Ink_iu : uint256
  Art_iu : uint256
  Gem_iu : uint256
  Art_i  : uint256
  Rate_i : uint256
  Sin_w  : uint256
  Vice   : uint256

storage
  live |-> Live
  vow  |-> Vow
  vat  |-> Vat

storage Vat
  wards[ACCT_ID]           |-> Ward
  urns[ilk][CALLER_ID].ink |-> Ink_iu => 0
  urns[ilk][CALLER_ID].art |-> Art_iu
  gem[ilk][CALLER_ID]      |-> Gem_iu => Gem_iu + Ink_iu
  ilks[ilk].Art            |-> Art_i
  ilks[ilk].rate           |-> Rate_i
  sin[Vow]                 |-> Sin_w
  vice                     |-> Vice

iff
  VCallValue == 0
  VCallDepth < 1024
  Live == 0
  Ward == 1
  Art_iu == 0
  Ink_iu <= posMinSInt256

iff in range uint256
  Gem_iu + Ink_iu

iff in range int256
  Rate_i

calls
  Vat.urns
  Vat.grab
```


```act
behaviour flow of End
interface flow(bytes32 ilk)

for all
  Vat    : address VatLike
  Debt   : uint256
  Fix    : uint256
  Gap    : uint256
  Art    : uint256
  Tag    : uint256
  Art_i  : uint256
  Rate_i : uint256
  Spot_i : uint256
  Line_i : uint256
  Dust_i : uint256


storage
  vat      |-> Vat
  debt     |-> Debt
  gap[ilk] |-> Gap
  Art[ilk] |-> Art
  tag[ilk] |-> Tag
  fix[ilk] |-> Fix => (((((((Art * Rate_i) / #Ray) * Tag) / #Ray) - Gap) * #Ray) * #Ray) / Debt

storage Vat
  ilks[ilk].Art  |-> Art_i
  ilks[ilk].rate |-> Rate_i
  ilks[ilk].spot |-> Spot_i
  ilks[ilk].line |-> Line_i
  ilks[ilk].dust |-> Dust_i

iff
  Debt =/= 0
  Fix == 0
  VCallValue == 0
  VCallDepth < 1024

iff in range uint256
  Art * Rate_i
  ((Art * Rate_i) / #Ray) * Tag
  ((((Art * Rate_i) / #Ray) * Tag) / #Ray) - Gap
  (((((Art * Rate_i) / #Ray) * Tag) / #Ray) - Gap) * #Ray
  ((((((Art * Rate_i) / #Ray) * Tag) / #Ray) - Gap) * #Ray) * #Ray

calls
  End.muluu
  End.subuu
  End.rmul
  End.rdiv
  Vat.ilks
```

```act
behaviour pack of End
interface pack(uint256 wad)

for all
  Vat  : address VatLike
  Vow  : address
  Debt : uint256
  Bag  : uint256
  Joy  : uint256
  Dai  : uint256
  Can  : uint256

storage
  vat  |-> Vat
  vow  |-> Vow
  debt |-> Debt
  bag[CALLER_ID] |-> Bag => Bag + wad

storage Vat
  can[CALLER_ID][ACCT_ID] |-> Can
  dai[CALLER_ID]          |-> Dai => Dai - wad * #Ray
  dai[Vow]                |-> Joy => Joy + wad * #Ray

iff
  Debt =/= 0
  Can  == 1
  VCallValue == 0
  VCallDepth < 1024

if
  CALLER_ID =/= Vow
  CALLER_ID =/= ACCT_ID

iff in range uint256
  Bag + wad
  wad * #Ray
  Dai - (wad * #Ray)
  Joy + (wad * #Ray)

calls
  End.muluu
  End.adduu
  Vat.move-diff
```

```act
behaviour cash of End
interface cash(bytes32 ilk, uint wad)

for all
  Vat   : address VatLike
  Fix   : uint256
  Bag   : uint256
  Out   : uint256
  Gem_e : uint256
  Gem_c : uint256

storage
  vat                 |-> Vat
  fix[ilk]            |-> Fix
  bag[CALLER_ID]      |-> Bag
  out[ilk][CALLER_ID] |-> Out => Out + wad

storage Vat
  can[ACCT_ID][ACCT_ID] |-> _
  gem[ilk][ACCT_ID]   |-> Gem_e => Gem_e - #rmul(wad, Fix)
  gem[ilk][CALLER_ID] |-> Gem_c => Gem_c + #rmul(wad, Fix)

iff
  Fix =/= 0
  Out + wad <= Bag
  VCallValue == 0
  VCallDepth < 1024

iff in range uint256
  wad * Fix
  Gem_e - ((wad * Fix) / #Ray)
  Gem_c + ((wad * Fix) / #Ray)

if
  ACCT_ID =/= CALLER_ID

calls
  End.adduu
  End.rmul
  Vat.flux-diff
```
