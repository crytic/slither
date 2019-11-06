```act
behaviour adduu of Vow
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
behaviour subuu of Vow
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
behaviour minuu of Vow
interface min(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : #if x > y #then y #else x #fi : WS

if

    #sizeWordStack(WS) <= 1000
```

### Accessors

#### owners

```act
behaviour wards of Vow
interface wards(address usr)

for all

    May : uint256

storage

    wards[usr] |-> May

iff

    VCallValue == 0

returns May
```

#### getting the `Vat`

```act
behaviour vat of Vow
interface vat()

for all

    Vat : address

storage

    vat |-> Vat

iff

    VCallValue == 0

returns Vat
```

#### getting the `Flapper`

```act
behaviour flapper of Vow
interface flapper()

for all

    Flapper : address

storage

    flapper |-> Flapper

iff

    VCallValue == 0

returns Flapper
```

#### getting the `Flopper`

```act
behaviour flopper of Vow
interface flopper()

for all

    Flopper : address

storage

    flopper |-> Flopper

iff

    VCallValue == 0

returns Flopper
```

#### getting a `sin` packet

```act
behaviour sin of Vow
interface sin(uint256 era)

for all

    Sin_era : uint256

storage

    sin[era] |-> Sin_era

iff

    VCallValue == 0

returns Sin_era
```

#### getting the `Sin`

```act
behaviour Sin of Vow
interface Sin()

for all

    Sin : uint256

storage

    Sin |-> Sin

iff

    VCallValue == 0

returns Sin
```

#### getting the `Ash`

```act
behaviour Ash of Vow
interface Ash()

for all

    Ash : uint256

storage

    Ash |-> Ash

iff

    VCallValue == 0

returns Ash
```

#### getting the `wait`

```act
behaviour wait of Vow
interface wait()

for all

    Wait : uint256

storage

    wait |-> Wait

iff

    VCallValue == 0

returns Wait
```

#### getting the `sump`

```act
behaviour sump of Vow
interface sump()

for all

    Sump : uint256

storage

    sump |-> Sump

iff

    VCallValue == 0

returns Sump
```

#### getting the `bump`

```act
behaviour bump of Vow
interface bump()

for all

    Bump : uint256

storage

    bump |-> Bump

iff

    VCallValue == 0

returns Bump
```

#### getting the `hump`

```act
behaviour hump of Vow
interface hump()

for all

    Hump : uint256

storage

    hump |-> Hump

iff

    VCallValue == 0

returns Hump
```

#### getting the `live` flag

```act
behaviour live of Vow
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

#### adding and removing owners

```act
behaviour rely-diff of Vow
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
behaviour rely-same of Vow
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
behaviour deny-diff of Vow
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
behaviour deny-same of Vow
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

#### setting `Vow` parameters

```act
behaviour file-data of Vow
interface file(bytes32 what, uint256 data)

for all

    May  : uint256
    Wait : uint256
    Sump : uint256
    Bump : uint256
    Hump : uint256

storage

    wards[CALLER_ID] |-> May
    wait             |-> Wait => (#if what == #string2Word("wait") #then data #else Wait #fi)
    sump             |-> Sump => (#if what == #string2Word("sump") #then data #else Sump #fi)
    bump             |-> Bump => (#if what == #string2Word("bump") #then data #else Bump #fi)
    hump             |-> Hump => (#if what == #string2Word("hump") #then data #else Hump #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0
```

#### cancelling bad debt and surplus

```act
behaviour heal of Vow
interface heal(uint256 rad)

for all

    Vat  : address VatLike
    Ash  : uint256
    Sin  : uint256
    Joy  : uint256
    Awe  : uint256
    Vice : uint256
    Debt : uint256

storage

    vat |-> Vat
    Ash |-> Ash
    Sin |-> Sin

storage Vat

    dai[ACCT_ID] |-> Joy  => Joy  - rad
    sin[ACCT_ID] |-> Awe  => Awe  - rad
    vice         |-> Vice => Vice - rad
    debt         |-> Debt => Debt - rad

iff

    rad <= Joy
    rad <= (Awe - Sin) - Ash
    VCallValue == 0
    VCallDepth < 1024

iff in range uint256

    (Awe - Sin) - Ash
    Joy  - rad
    Awe  - rad
    Vice - rad
    Debt - rad

calls

  Vow.subuu
  Vat.dai
  Vat.sin
  Vat.heal
```

```act
behaviour kiss of Vow
interface kiss(uint256 rad)

for all

    Vat  : address VatLike
    Ash  : uint256
    Joy  : uint256
    Awe  : uint256
    Vice : uint256
    Debt : uint256

storage

    vat |-> Vat
    Ash |-> Ash => Ash - rad

storage Vat

    dai[ACCT_ID] |-> Joy  => Joy  - rad
    sin[ACCT_ID] |-> Awe  => Awe  - rad
    vice         |-> Vice => Vice - rad
    debt         |-> Debt => Debt - rad

iff

    rad <= Joy
    rad <= Ash
    VCallValue == 0
    VCallDepth < 1024

iff in range uint256

    Ash  - rad
    Joy  - rad
    Awe  - rad
    Vice - rad
    Debt - rad

calls

  Vow.subuu
  Vat.dai
  Vat.heal
```

#### adding to the `sin` queue

```act
behaviour fess of Vow
interface fess(uint256 tab)

for all

    May     : uint256
    Sin_era : uint256
    Sin     : uint256

storage

    wards[CALLER_ID] |-> May
    sin[TIME]        |-> Sin_era => Sin_era + tab
    Sin              |-> Sin     => Sin     + tab

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0

iff in range uint256

    Sin_era + tab
    Sin     + tab

calls

  Vow.adduu
```

#### processing `sin` queue

```act
behaviour flog of Vow
interface flog(uint256 t)

for all

    Wait  : uint256
    Sin_t : uint256
    Sin   : uint256

storage

    wait   |-> Wait
    Sin    |-> Sin   => Sin - Sin_t
    sin[t] |-> Sin_t => 0

iff

    // act: `sin` has `. ? : not` matured
    t + Wait <= TIME
    VCallValue == 0

iff in range uint256

    t   + Wait
    Sin - Sin_t

calls

  Vow.adduu
  Vow.subuu
```

#### starting a debt auction

```act
behaviour flop of Vow
interface flop()

for all

    Flopper  : address Flopper
    Vat      : address VatLike
    MayFlop  : uint256
    Sin      : uint256
    Ash      : uint256
    Awe      : uint256
    Joy      : uint256
    Sump     : uint256
    Kicks    : uint256
    FlopLive : uint256
    Ttl      : uint48
    Tau      : uint48
    Bid      : uint256
    Lot      : uint256
    Guy      : address
    Tic      : uint48
    End      : uint48

storage

    flopper |-> Flopper
    vat     |-> Vat
    Sin     |-> Sin
    Ash     |-> Ash => Ash + Sump
    sump    |-> Sump

storage Flopper

    live                        |-> FlopLive
    wards[ACCT_ID]              |-> MayFlop
    kicks                       |-> Kicks => 1 + Kicks
    ttl_tau                     |-> #WordPackUInt48UInt48(Ttl, Tau)
    bids[1 + Kicks].bid         |-> Bid => Sump
    bids[1 + Kicks].lot         |-> Lot => maxUInt256
    bids[1 + Kicks].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => #WordPackAddrUInt48UInt48(ACCT_ID, Tic, TIME + Tau)

storage Vat

    dai[ACCT_ID] |-> Joy
    sin[ACCT_ID] |-> Awe

iff

    FlopLive == 1
    MayFlop == 1
    (Awe - Sin) - Ash >= Sump
    Joy == 0
    // act: call stack is not too big
    VCallDepth < 1024
    VCallValue == 0

iff in range uint48

    TIME + Tau

iff in range uint256

    Ash + Sump
    Awe - Sin
    (Awe - Sin) - Ash
    1 + Kicks

if

    #rangeUInt(48, TIME)


returns 1 + Kicks

calls

  Vow.subuu
  Vow.adduu
  Vat.sin
  Vat.dai
  Flopper.kick
```

#### starting a surplus auction

```act
behaviour flap of Vow
interface flap()

for all

    Flapper  : address Flapper
    Vat      : address VatLike
    FlapVat  : address
    Sin      : uint256
    Ash      : uint256
    Awe      : uint256
    Joy      : uint256
    Bump     : uint256
    Hump     : uint256
    Can      : uint256
    Dai_a    : uint256
    FlapLive : uint256
    Kicks    : uint256
    Ttl      : uint48
    Tau      : uint48
    Bid      : uint256
    Lot      : uint256
    Guy      : address
    Tic      : uint48
    End      : uint48

storage

    vat     |-> Vat
    flapper |-> Flapper
    bump    |-> Bump
    hump    |-> Hump
    Sin     |-> Sin
    Ash     |-> Ash

storage Flapper

    vat                         |-> FlapVat
    kicks                       |-> Kicks   => 1 + Kicks
    ttl_tau                     |-> #WordPackUInt48UInt48(Ttl, Tau)
    bids[1 + Kicks].bid         |-> Bid => 0
    bids[1 + Kicks].lot         |-> Lot => Bump
    bids[1 + Kicks].guy_tic_end |-> #WordPackAddrUInt48UInt48(Guy, Tic, End) => #WordPackAddrUInt48UInt48(ACCT_ID, Tic, TIME + Tau)
    live                        |-> FlapLive

storage Vat

    can[ACCT_ID][Flapper] |-> Can
    sin[ACCT_ID]          |-> Awe
    dai[ACCT_ID]          |-> Joy   => Joy   - Bump
    dai[Flapper]          |-> Dai_a => Dai_a + Bump

iff

    VCallValue == 0
    VCallDepth < 1023
    Joy >= (Awe + Bump) + Hump
    (Awe - Sin) - Ash == 0
    FlapLive == 1
    Can == 1

iff in range uint256

    1 + Kicks
    Dai_a + Bump

iff in range uint48

    TIME + Tau

if

    #rangeUInt(48, TIME)
    Flapper =/= Vat
    ACCT_ID =/= Vat
    ACCT_ID =/= Flapper
    FlapVat ==  Vat

calls

    Vow.subuu
    Vow.adduu
    Vat.dai
    Vat.sin
    Flapper.kick

returns 1 + Kicks
```

#### system lock down

```act
behaviour cage-surplus of Vow
interface cage()

for all

    Vat      : address VatLike
    Flapper  : address Flapper
    Flopper  : address Flopper
    FlapVat  : address
    MayFlap  : uint256
    MayFlop  : uint256
    Dai_v    : uint256
    Sin_v    : uint256
    Dai_f    : uint256
    Debt     : uint256
    Vice     : uint256
    Live     : uint256
    Sin      : uint256
    Ash      : uint256
    FlapLive : uint256
    FlopLive : uint256

storage

    wards[CALLER_ID] |-> Can
    vat |-> Vat
    flopper |-> Flopper
    flapper |-> Flapper
    live |-> Live => 0
    Sin  |-> Sin  => 0
    Ash  |-> Ash  => 0

storage Vat

    can[Flapper][Flapper] |-> _
    dai[Flapper] |-> Dai_f => 0
    dai[ACCT_ID] |-> Dai_v => (Dai_v + Dai_f) - Sin_v
    sin[ACCT_ID] |-> Sin_v => 0
    debt |-> Debt => Debt - Sin_v
    vice |-> Vice => Vice - Sin_v

storage Flapper

    wards[ACCT_ID] |-> MayFlap
    vat  |-> FlapVat
    live |-> FlapLive => 0

storage Flopper

    wards[ACCT_ID] |-> MayFlop
    live |-> FlopLive => 0

iff

    VCallValue == 0
    VCallDepth < 1023
    Can == 1
    MayFlap == 1
    MayFlop == 1

iff in range uint256

    Dai_v + Dai_f
    Debt - Sin_v
    Vice - Sin_v

if

    Dai_v + Dai_f > Sin_v
    Flapper =/= ACCT_ID
    Flapper =/= Vat
    Flopper =/= ACCT_ID
    Flopper =/= Vat
    Flopper =/= Flapper
    FlapVat ==  Vat

calls

  Vow.minuu
  Vat.dai
  Vat.sin
  Vat.heal
  Flapper.cage
  Flopper.cage
```

```act
behaviour cage-deficit of Vow
interface cage()

for all

    Vat     : address VatLike
    Flapper : address Flapper
    Flopper : address Flopper
    FlapVat : address
    MayFlap : uint256
    MayFlop : uint256
    Dai_v   : uint256
    Sin_v   : uint256
    Dai_f   : uint256
    Debt    : uint256
    Vice    : uint256
    Live     : uint256
    Sin      : uint256
    Ash      : uint256
    FlapLive : uint256
    FlopLive : uint256

storage

    wards[CALLER_ID] |-> Can
    vat |-> Vat
    flopper |-> Flopper
    flapper |-> Flapper
    live |-> Live => 0
    Sin  |-> Sin => 0
    Ash  |-> Ash => 0

storage Vat

    can[Flapper][Flapper] |-> _
    dai[Flapper] |-> Dai_f => 0
    dai[ACCT_ID] |-> Dai_v => 0
    sin[ACCT_ID] |-> Sin_v => Sin_v - (Dai_v + Dai_f)
    debt |-> Debt => Debt - (Dai_v + Dai_f)
    vice |-> Vice => Vice - (Dai_v + Dai_f)

storage Flapper

    wards[ACCT_ID] |-> MayFlap
    vat  |-> FlapVat
    live |-> FlapLive => 0

storage Flopper

    wards[ACCT_ID] |-> MayFlop
    live |-> FlopLive => 0

iff

    VCallValue == 0
    VCallDepth < 1023
    Can == 1
    MayFlap == 1
    MayFlop == 1

iff in range uint256

    Debt - (Dai_v + Dai_f)
    Vice - (Dai_v + Dai_f)

if

    Dai_v + Dai_f < Sin_v
    Flapper =/= ACCT_ID
    Flapper =/= Vat
    Flopper =/= ACCT_ID
    Flopper =/= Vat
    Flopper =/= Flapper
    FlapVat ==  Vat

calls

  Vow.minuu
  Vat.dai
  Vat.sin
  Vat.heal
  Flapper.cage
  Flopper.cage
```

```act
behaviour cage-balance of Vow
interface cage()

for all

    Vat     : address VatLike
    Flapper : address Flapper
    Flopper : address Flopper
    FlapVat : address
    MayFlap : uint256
    MayFlop : uint256
    Dai_v   : uint256
    Sin_v   : uint256
    Dai_f   : uint256
    Debt    : uint256
    Vice    : uint256
    Live     : uint256
    Sin      : uint256
    Ash      : uint256
    FlapLive : uint256
    FlopLive : uint256

storage

    wards[CALLER_ID] |-> Can
    vat |-> Vat
    flopper |-> Flopper
    flapper |-> Flapper
    live |-> Live => 0
    Sin  |-> Sin => 0
    Ash  |-> Ash => 0

storage Vat

    can[Flapper][Flapper] |-> _
    dai[Flapper] |-> Dai_f => 0
    dai[ACCT_ID] |-> Dai_v => 0
    sin[ACCT_ID] |-> Sin_v => 0
    debt |-> Debt => Debt - (Dai_v + Dai_f)
    vice |-> Vice => Vice - Sin_v

storage Flapper

    wards[ACCT_ID] |-> MayFlap
    vat  |-> FlapVat
    live |-> FlapLive => 0

storage Flopper

    wards[ACCT_ID] |-> MayFlop
    live |-> FlopLive => 0

iff

    VCallValue == 0
    VCallDepth < 1023
    Can == 1
    MayFlap == 1
    MayFlop == 1

iff in range uint256

    Dai_v + Dai_f
    Debt - (Dai_v + Dai_f)
    Vice - Sin_v

if

    Dai_v + Dai_f == Sin_v
    Flapper =/= ACCT_ID
    Flapper =/= Vat
    Flopper =/= ACCT_ID
    Flopper =/= Vat
    Flopper =/= Flapper
    FlapVat ==  Vat

calls

  Vow.minuu
  Vat.dai
  Vat.sin
  Vat.heal
  Flapper.cage
  Flopper.cage
```
