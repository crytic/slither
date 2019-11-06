```act
behaviour wards of Vat
interface wards(address usr)

for all

    May : uint256

storage

    wards[usr] |-> May

iff

    VCallValue == 0

returns May
```

#### allowances

```act
behaviour can of Vat
interface can(address src, address dst)

for all

    Can : uint256

storage

    can[src][dst] |-> Can

iff

    VCallValue == 0

returns Can
```

#### collateral type data

An `ilk` is a collateral type.

```act
behaviour ilks of Vat
interface ilks(bytes32 ilk)

for all

    Ilk_Art  : uint256
    Ilk_rate : uint256
    Ilk_spot : uint256
    Ilk_line : uint256
    Ilk_dust : uint256

storage

    ilks[ilk].Art  |-> Ilk_Art
    ilks[ilk].rate |-> Ilk_rate
    ilks[ilk].spot |-> Ilk_spot
    ilks[ilk].line |-> Ilk_line
    ilks[ilk].dust |-> Ilk_dust

iff

    VCallValue == 0

returns Ilk_Art : Ilk_rate : Ilk_spot : Ilk_line : Ilk_dust
```

#### `urn` data

An `urn` is a collateralised debt position.

```act
behaviour urns of Vat
interface urns(bytes32 ilk, address urn)

for all

    Ink_iu : uint256
    Art_iu : uint256

storage

    urns[ilk][urn].ink |-> Ink_iu
    urns[ilk][urn].art |-> Art_iu

iff

    VCallValue == 0

returns Ink_iu : Art_iu
```

#### internal unencumbered collateral balances

A `gem` is a token used as collateral in some `ilk`.

```act
behaviour gem of Vat
interface gem(bytes32 ilk, address usr)

for all

    Gem : uint256

storage

    gem[ilk][usr] |-> Gem

iff

    VCallValue == 0

returns Gem
```

#### internal dai balances

`dai` is a stablecoin.

```act
behaviour dai of Vat
interface dai(address usr)

for all

    Rad : uint256

storage

    dai[usr] |-> Rad

iff

    VCallValue == 0

returns Rad
```

#### internal sin balances

`sin`, or "system debt", is used to track debt which is no longer assigned to a particular CDP, and is carried by the system during the liquidation process.

```act
behaviour sin of Vat
interface sin(address usr)

for all

    Rad : uint256

storage

    sin[usr] |-> Rad

iff

    VCallValue == 0

returns Rad
```

#### total debt

```act
behaviour debt of Vat
interface debt()

for all

    Debt : uint256

storage

    debt |-> Debt

iff

    VCallValue == 0

returns Debt
```

#### total bad debt

```act
behaviour vice of Vat
interface vice()

for all

    Vice : uint256

storage

    vice |-> Vice

iff

    VCallValue == 0

returns Vice
```

#### debt ceiling

```act
behaviour Line of Vat
interface Line()

for all

    Line : uint256

storage

    Line |-> Line

iff

    VCallValue == 0

returns Line
```

#### system liveness flag

```act
behaviour live of Vat
interface live()

for all

    Live : uint256

storage

    live |-> Live

iff

    VCallValue == 0

returns Live
```

### Lemmas

#### Arithmetic

```act
behaviour addui of Vat
interface add(uint256 x, int256 y) internal

stack

   #unsigned(y) : x : JMPTO : WS => JMPTO : x + y : WS

iff in range uint256

   x + y

if

   #sizeWordStack(WS) <= 1015
```

```act
behaviour subui of Vat
interface sub(uint256 x, int256 y) internal

stack

    #unsigned(y) : x : JMPTO : WS => JMPTO : x - y : WS

iff in range uint256

    x - y

if

    #sizeWordStack(WS) <= 1015
```

```act
behaviour mului of Vat
interface mul(uint256 x, int256 y) internal

stack

    #unsigned(y) : x : JMPTO : WS => JMPTO : #unsigned(x * y) : WS

iff in range int256

    x
    x * y

if

    // TODO: strengthen
    #sizeWordStack(WS) <= 1000
```
```act
behaviour adduu of Vat
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
behaviour subuu of Vat
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
behaviour muluu of Vat
interface mul(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : x * y : WS

iff in range uint256

    x * y

if

    // TODO: strengthen
    #sizeWordStack(WS) <= 1000
```

### Mutators

#### Set global settlement

Freezes the price of all positions.


```act
behaviour cage of Vat
interface cage()

for all

    May   : uint256
    Lives : uint256

storage

    wards[CALLER_ID] |-> May
    live             |-> Lives => 0

iff

    VCallValue == 0
    May == 1
```



#### adding and removing owners

Any owner can add and remove owners.

```act
behaviour rely-diff of Vat
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
behaviour rely-same of Vat
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
behaviour deny-diff of Vat
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
behaviour deny-same of Vat
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
behaviour hope of Vat
interface hope(address usr)

storage

    can[CALLER_ID][usr] |-> _ => 1

iff

    VCallValue == 0
```

```act
behaviour nope of Vat
interface nope(address usr)

storage

    can[CALLER_ID][usr] |-> _ => 0

iff

    VCallValue == 0
```

#### initialising an `ilk`

An `ilk` starts with `Rate` set to (fixed-point) one.

```act
behaviour init of Vat
interface init(bytes32 ilk)

for all

    May  : uint256
    Rate : uint256

storage

    wards[CALLER_ID] |-> May
    ilks[ilk].rate   |-> Rate => #Ray

iff

    // act: caller is `. ? : not` authorised
    May == 1
    // act: `Rate` is `. ? : not` zero
    Rate == 0
    VCallValue == 0
```

#### setting the debt ceiling

```act
behaviour file of Vat
interface file(bytes32 what, uint256 data)

for all

    May  : uint256
    Line : uint256

storage

    wards[CALLER_ID] |-> May
    Line             |-> Line => (#if what == #string2Word("Line") #then data #else Line #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0
```

#### setting `Ilk` data

```act
behaviour file-ilk of Vat
interface file(bytes32 ilk, bytes32 what, uint256 data)

for all

    May  : uint256
    Spot : uint256
    Line : uint256
    Dust : uint256

storage

    wards[CALLER_ID] |-> May
    ilks[ilk].spot   |-> Spot => (#if what == #string2Word("spot") #then data #else Spot #fi)
    ilks[ilk].line   |-> Line => (#if what == #string2Word("line") #then data #else Line #fi)
    ilks[ilk].dust   |-> Dust => (#if what == #string2Word("dust") #then data #else Dust #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0
```

#### assigning unencumbered collateral

Collateral coming from outside of the system must be assigned to a user before it can be locked in a CDP.

```act
behaviour slip of Vat
interface slip(bytes32 ilk, address usr, int256 wad)

for all

    May : uint256
    Gem : uint256

storage

    wards[CALLER_ID] |-> May
    gem[ilk][usr]    |-> Gem => Gem + wad

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0

iff in range uint256

    Gem + wad

calls

    Vat.addui
```

#### moving unencumbered collateral

```act
behaviour flux-diff of Vat
interface flux(bytes32 ilk, address src, address dst, uint256 wad)

for all

    May     : uint256
    Gem_src : uint256
    Gem_dst : uint256

storage

    can[src][CALLER_ID] |-> May
    gem[ilk][src]       |-> Gem_src => Gem_src - wad
    gem[ilk][dst]       |-> Gem_dst => Gem_dst + wad

iff

    // act: caller is `. ? : not` authorised
    (May == 1 or src == CALLER_ID)
    VCallValue == 0

iff in range uint256

    Gem_src - wad
    Gem_dst + wad

if

    src =/= dst

calls

    Vat.subuu
    Vat.adduu
```

```act
behaviour flux-same of Vat
interface flux(bytes32 ilk, address src, address dst, uint256 wad)

for all

    May     : uint256
    Gem_src : uint256

storage

    can[src][CALLER_ID] |-> May
    gem[ilk][src]       |-> Gem_src => Gem_src

iff

    // act: caller is `. ? : not` authorised
    (May == 1 or src == CALLER_ID)
    VCallValue == 0

iff in range uint256

    Gem_src - wad

if

    src == dst

calls

    Vat.subuu
    Vat.adduu
```

#### transferring dai balances

```act
behaviour move-diff of Vat
interface move(address src, address dst, uint256 rad)

for all

    Dai_dst : uint256
    Dai_src : uint256
    May     : uint256

storage

    can[src][CALLER_ID] |-> May
    dai[src]            |-> Dai_src => Dai_src - rad
    dai[dst]            |-> Dai_dst => Dai_dst + rad

iff

    // act: caller is `. ? : not` authorised
    (May == 1 or src == CALLER_ID)
    VCallValue == 0

iff in range uint256

    Dai_src - rad
    Dai_dst + rad

if

    src =/= dst

calls

  Vat.adduu
  Vat.subuu
```

```act
behaviour move-same of Vat
interface move(address src, address dst, uint256 rad)

for all

    Dai_src : uint256
    May     : uint256

storage

    can[src][CALLER_ID] |-> May
    dai[src]            |-> Dai_src => Dai_src

iff

    // act: caller is `. ? : not` authorised
    (May == 1 or src == CALLER_ID)
    VCallValue == 0

iff in range uint256

    Dai_src - rad

if

    src == dst

calls

    Vat.subuu
    Vat.adduu
```

#### administering a position

This is the core method that opens, manages, and closes a collateralised debt position. This method has the ability to issue or delete dai while increasing or decreasing the position's debt, and to deposit and withdraw "encumbered" collateral from the position. The caller specifies the ilk `i` to interact with, and identifiers `u`, `v`, and `w`, corresponding to the sources of the debt, unencumbered collateral, and dai, respectively. The collateral and debt unit adjustments `dink` and `dart` are specified incrementally.

```act
behaviour frob-diff of Vat
interface frob(bytes32 i, address u, address v, address w, int dink, int dart)

for all

    Ilk_rate : uint256
    Ilk_line : uint256
    Ilk_spot : uint256
    Ilk_dust : uint256
    Ilk_Art  : uint256
    Urn_ink  : uint256
    Urn_art  : uint256
    Gem_iv   : uint256
    Dai_w    : uint256
    Debt     : uint256
    Line     : uint256
    Can_u    : uint256
    Can_v    : uint256
    Can_w    : uint256
    Live     : uint256

storage

    ilks[i].rate      |-> Ilk_rate
    ilks[i].line      |-> Ilk_line
    ilks[i].spot      |-> Ilk_spot
    ilks[i].dust      |-> Ilk_dust
    Line              |-> Line
    can[u][CALLER_ID] |-> Can_u
    can[v][CALLER_ID] |-> Can_v
    can[w][CALLER_ID] |-> Can_w
    urns[i][u].ink    |-> Urn_ink  => Urn_ink + dink
    urns[i][u].art    |-> Urn_art  => Urn_art + dart
    ilks[i].Art       |-> Ilk_Art  => Ilk_Art + dart
    gem[i][v]         |-> Gem_iv   => Gem_iv  - dink
    dai[w]            |-> Dai_w    => Dai_w + (Ilk_rate * dart)
    debt              |-> Debt     => Debt  + (Ilk_rate * dart)
    live              |-> Live

iff in range uint256

    Urn_ink + dink
    Urn_art + dart
    Ilk_Art + dart
    Gem_iv  - dink
    Dai_w + (Ilk_rate * dart)
    Debt  + (Ilk_rate * dart)
    (Urn_art + dart) * Ilk_rate
    (Urn_ink + dink) * Ilk_spot
    (Ilk_Art + dart) * Ilk_rate

iff in range int256

    Ilk_rate
    Ilk_rate * dart

iff
    VCallValue == 0
    (dart <= 0) or (((Ilk_Art + dart) * Ilk_rate <= Ilk_line) and ((Debt + Ilk_rate * dart) <= Line))
    (dart <= 0 and dink >= 0) or ((((Urn_art + dart) * Ilk_rate) <= ((Urn_ink + dink) * Ilk_spot)))
    (dart <= 0 and dink >= 0) or (u == CALLER_ID or Can_u == 1)
    (dink <= 0) or (v == CALLER_ID or Can_v == 1)
    (dart >= 0) or (w == CALLER_ID or Can_w == 1)
    ((Urn_art + dart) == 0) or (((Urn_art + dart) * Ilk_rate) >= Ilk_dust)
    Ilk_rate =/= 0
    Live == 1

if

    u =/= v
    v =/= w
    u =/= w

calls

    Vat.addui
    Vat.subui
    Vat.mului
    Vat.muluu
```

```act
behaviour frob-same of Vat
interface frob(bytes32 i, address u, address v, address w, int dink, int dart)

for all

    Ilk_rate : uint256
    Ilk_line : uint256
    Ilk_spot : uint256
    Ilk_dust : uint256
    Ilk_Art  : uint256
    Urn_ink  : uint256
    Urn_art  : uint256
    Gem_iu   : uint256
    Dai_u    : uint256
    Debt     : uint256
    Line     : uint256
    Can_u    : uint256
    Live     : uint256

storage

    ilks[i].rate      |-> Ilk_rate
    ilks[i].line      |-> Ilk_line
    ilks[i].spot      |-> Ilk_spot
    ilks[i].dust      |-> Ilk_dust
    Line              |-> Line
    can[u][CALLER_ID] |-> Can_u
    urns[i][u].ink    |-> Urn_ink  => Urn_ink + dink
    urns[i][u].art    |-> Urn_art  => Urn_art + dart
    ilks[i].Art       |-> Ilk_Art  => Ilk_Art + dart
    gem[i][u]         |-> Gem_iu   => Gem_iu  - dink
    dai[u]            |-> Dai_u    => Dai_u + (Ilk_rate * dart)
    debt              |-> Debt     => Debt  + (Ilk_rate * dart)
    live              |-> Live

iff in range uint256

    Urn_ink + dink
    Urn_art + dart
    Ilk_Art + dart
    Gem_iv  - dink
    Dai_w + (Ilk_rate * dart)
    Debt  + (Ilk_rate * dart)
    (Urn_art + dart) * Ilk_rate
    (Urn_ink + dink) * Ilk_spot
    (Ilk_Art + dart) * Ilk_rate

iff in range int256

    Ilk_rate
    Ilk_rate * dart

iff

    VCallValue == 0
    (dart <= 0) or (((Ilk_Art + dart) * Ilk_rate <= Ilk_line) and ((Debt + Ilk_rate * dart) <= Line))
    (dart <= 0 and dink >= 0) or (((Urn_art + dart) * Ilk_rate) <= ((Urn_ink + dink) * Ilk_spot))
    u == CALLER_ID or Can_u == 1
    ((Urn_art + dart) == 0) or (((Urn_art + dart) * Ilk_rate) >= Ilk_dust)
    Ilk_rate =/= 0
    Live == 1

if

    u == v
    v == w
    u == w

calls

    Vat.addui
    Vat.subui
    Vat.mului
    Vat.muluu
```

#### forking a position

```act
behaviour fork-diff of Vat
interface fork(bytes32 ilk, address src, address dst, int256 dink, int256 dart)

for all

    Can_src : uint256
    Can_dst : uint256
    Rate    : uint256
    Spot    : uint256
    Dust    : uint256
    Ink_u   : uint256
    Art_u   : uint256
    Ink_v   : uint256
    Art_v   : uint256

storage

    can[src][CALLER_ID] |-> Can_src
    can[dst][CALLER_ID] |-> Can_dst
    ilks[ilk].rate      |-> Rate
    ilks[ilk].spot      |-> Spot
    ilks[ilk].dust      |-> Dust
    urns[ilk][src].ink  |-> Ink_u => Ink_u - dink
    urns[ilk][src].art  |-> Art_u => Art_u - dart
    urns[ilk][dst].ink  |-> Ink_v => Ink_v + dink
    urns[ilk][dst].art  |-> Art_v => Art_v + dart

iff
    VCallValue == 0

    (src == CALLER_ID) or (Can_src == 1)
    (dst == CALLER_ID) or (Can_dst == 1)

    (Art_u - dart) * Rate <= (Ink_u - dink) * Spot
    (Art_v + dart) * Rate <= (Ink_v + dink) * Spot

    ((Art_u - dart) * Rate >= Dust) or (Art_u - dart == 0)
    ((Art_v + dart) * Rate >= Dust) or (Art_v + dart == 0)

iff in range uint256

    Ink_u - dink
    Ink_v + dink
    Art_u - dart
    Art_v + dart
    (Ink_u - dink) * Spot
    (Ink_v + dink) * Spot

if

    src =/= dst

calls

    Vat.addui
    Vat.subui
    Vat.muluu
```

```act
behaviour fork-same of Vat
interface fork(bytes32 ilk, address src, address dst, int256 dink, int256 dart)

for all

    Can_src : uint256
    Rate    : uint256
    Spot    : uint256
    Dust    : uint256
    Ink_u   : uint256
    Art_u   : uint256

storage

    can[src][CALLER_ID] |-> Can_src
    ilks[ilk].rate      |-> Rate
    ilks[ilk].spot      |-> Spot
    ilks[ilk].dust      |-> Dust
    urns[ilk][src].ink  |-> Ink_u => Ink_u
    urns[ilk][src].art  |-> Art_u => Art_u


iff
    VCallValue == 0

    (dink >= 0) or (Ink_u - dink <= maxUInt256)
    (dink <= 0) or (Ink_u - dink >= 0)
    (dart >= 0) or (Art_u - dart <= maxUInt256)
    (dart <= 0) or (Art_u - dart >= 0)

    Ink_u * Spot <= maxUInt256

    (src == CALLER_ID) or (Can_src == 1)

    Art_u * Rate <= Ink_u * Spot
    (Art_u * Rate >= Dust) or (Art_u == 0)

if

    src == dst

calls

    Vat.addui
    Vat.subui
    Vat.muluu
```

#### confiscating a position

When a position of a user `u` is seized, both the collateral and debt are deleted from the user's account and assigned to the system's balance sheet, with the debt reincarnated as `sin` and assigned to some agent of the system `w`, while collateral goes to `v`.

```act
behaviour grab of Vat
interface grab(bytes32 i, address u, address v, address w, int256 dink, int256 dart)

for all

    May    : uint256
    Rate   : uint256
    Ink_iu : uint256
    Art_iu : uint256
    Art_i  : uint256
    Gem_iv : uint256
    Sin_w  : uint256
    Vice   : uint256

storage

    wards[CALLER_ID] |-> May
    ilks[i].Art      |-> Art_i  => Art_i  + dart
    ilks[i].rate     |-> Rate
    urns[i][u].ink   |-> Ink_iu => Ink_iu + dink
    urns[i][u].art   |-> Art_iu => Art_iu + dart
    gem[i][v]        |-> Gem_iv => Gem_iv - dink
    sin[w]           |-> Sin_w  => Sin_w  - (Rate * dart)
    vice             |-> Vice   => Vice   - (Rate * dart)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0

iff in range uint256

    Ink_iu + dink
    Art_iu + dart
    Art_i  + dart
    Gem_iv - dink
    Sin_w  - (Rate * dart)
    Vice   - (Rate * dart)

iff in range int256

    Rate
    Rate * dart

calls

    Vat.mului
    Vat.addui
    Vat.subui
```

#### annihilating system debt and surplus

`dai` and `sin` are two sides of the same coin. When the system has surplus `dai`, it can be cancelled with `sin`.

```act
behaviour heal of Vat
interface heal(uint256 rad)

for all

    Dai  : uint256
    Sin  : uint256
    Debt : uint256
    Vice : uint256

storage

    dai[CALLER_ID]   |-> Dai => Dai - rad
    sin[CALLER_ID]   |-> Sin => Sin - rad
    debt             |-> Debt  => Debt  - rad
    vice             |-> Vice  => Vice  - rad

iff

    VCallValue == 0

iff in range uint256

    Dai - rad
    Sin - rad
    Debt  - rad
    Vice  - rad

calls

    Vat.subuu
```
#### Creating system debt and surplus

Authorized actors can increase system debt to generate more dai.
```act
behaviour suck of Vat
interface suck(address u, address v, uint256 rad)

for all

    May   : uint256
    Dai_v : uint256
    Sin_u : uint256
    Debt  : uint256
    Vice  : uint256

storage

    wards[CALLER_ID] |-> May
    sin[u]           |-> Sin_u => Sin_u + rad
    dai[v]           |-> Dai_v => Dai_v + rad
    debt             |-> Debt  => Debt  + rad
    vice             |-> Vice  => Vice  + rad

iff

    May == 1
    VCallValue == 0

iff in range uint256

    Dai_v + rad
    Sin_u + rad
    Debt  + rad
    Vice  + rad

calls

    Vat.adduu
```

#### applying interest to an `ilk`

Interest is charged on an `ilk` `i` by adjusting the debt unit `Rate`, which says how many units of `dai` correspond to a unit of `art`. To preserve a key invariant, dai must be created or destroyed, depending on whether `Rate` is increasing or decreasing. The beneficiary/benefactor of the dai is `u`.

```act
behaviour fold of Vat
interface fold(bytes32 i, address u, int256 rate)

for all

    May    : uint256
    Rate_i : uint256
    Dai_u  : uint256
    Art_i  : uint256
    Debt   : uint256

storage

    wards[CALLER_ID] |-> May
    ilks[i].rate     |-> Rate_i => Rate_i + rate
    ilks[i].Art      |-> Art_i
    dai[u]           |-> Dai_u => Dai_u + Art_i * rate
    debt             |-> Debt  => Debt  + Art_i * rate
    live             |-> Live

iff

    VCallValue == 0
    May == 1
    Live == 1
    Art_i <= maxSInt256

iff in range int256

    Art_i * rate

iff in range uint256

    Rate_i + rate
    Dai_u  + (Art_i * rate)
    Debt   + (Art_i * rate)

calls

    Vat.addui
    Vat.mului
```
