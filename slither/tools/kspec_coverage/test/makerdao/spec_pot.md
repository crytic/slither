```act
behaviour adduu of Pot
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
behaviour subuu of Pot
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
behaviour muluu of Pot
interface mul(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : x * y : WS

iff in range uint256

    x * y

if

    #sizeWordStack(WS) <= 1000
```

```act
behaviour rmul of Pot
interface rmul(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : (x * y) / #Ray : WS

iff in range uint256

    x * y

if

    // TODO: strengthen
    #sizeWordStack(WS) <= 1000
```


### Accessors

#### owners

```act
behaviour wards of Pot
interface wards(address usr)

for all

    May : uint256

storage

    wards[usr] |-> May

iff

    VCallValue == 0

returns May
```

#### deposit balances

```act
behaviour pie of Pot
interface pie(address usr)

for all

    Pie_usr : uint256

storage

    pie[usr] |-> Pie_usr

iff

    VCallValue == 0

returns Pie_usr
```

#### total deposits

```act
behaviour Pie of Pot
interface Pie()

for all

    Pie_tot : uint256

storage

    Pie |-> Pie_tot

iff

    VCallValue == 0

returns Pie_tot
```

#### savings interest rate

```act
behaviour dsr of Pot
interface dsr()

for all

    Dsr : uint256

storage

    dsr |-> Dsr

iff

    VCallValue == 0

returns Dsr
```

#### savings interest rate accumulator

```act
behaviour chi of Pot
interface chi()

for all

    Chi : uint256

storage

    chi |-> Chi

iff

    VCallValue == 0

returns Chi
```

#### `Vat` address

```act
behaviour vat of Pot
interface vat()

for all

    Vat : address

storage

    vat |-> Vat

iff

    VCallValue == 0

returns Vat
```

#### `Vow` address

```act
behaviour vow of Pot
interface vow()

for all

    Vow : address

storage

    vow |-> Vow

iff

    VCallValue == 0

returns Vow
```

#### last `drip` time

```act
behaviour rho of Pot
interface rho()

for all

    Rho : uint256

storage

    rho |-> Rho

iff

    VCallValue == 0

returns Rho
```

### Mutators

#### adding and removing owners

```act
behaviour rely-diff of Pot
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
behaviour rely-same of Pot
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
behaviour deny-diff of Pot
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
behaviour deny-same of Pot
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

#### setting the savings rate

```act
behaviour file-dsr of Pot
interface file(bytes32 what, uint256 data)

for all

    May : uint256
    Dsr : uint256

storage

    wards[CALLER_ID] |-> May
    dsr              |-> Dsr => (#if what == #string2Word("dsr") #then data #else Dsr #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0
```

#### setting the `Vow` address

```act
behaviour file-vow of Pot
interface file(bytes32 what, address addr)

for all

    May : uint256
    Vow : address

storage

    wards[CALLER_ID] |-> May
    vow              |-> Vow => (#if what == #string2Word("vow") #then addr #else Vow #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0
```

#### `rpow`

```act
behaviour rpow-loop of Pot
lemma

//  0e01 => 0e45
pc

    3585 => 3653

for all

    Half   : uint256
    Z      : uint256
    Base   : uint256
    N      : uint256
    X      : uint256

stack

    _ : _ : Half : _ : Z : Base : N : X : WS => Half : _ : #rpow(Z, X, N, Base) : Base : 0 : _ : WS

gas

    194 + ((num0(N) * 172) + (num1(N) * 287))

if

    Half == Base / 2
    0 <= #rpow(Z, X, N, Base)
    #rpow(Z, X, N, Base) * Base < pow256
    N =/= 0
    Base =/= 0
    #sizeWordStack(WS) <= 1000
    num0(N) >= 0
    num1(N) >= 0
```


```act
behaviour rpow of Pot
interface rpow(uint256 x, uint256 n, uint256 b) internal

stack

    b : n : x : JMPTO : WS => JMPTO : #rpow(b, x, n, b) : WS

gas

    (#if ( ABI_x ==K 0 ) #then (#if ( ABI_n ==K 0 ) #then 82 #else 92 #fi) #else (#if ( ( ABI_n modInt 2 ) ==K 0 ) #then (#if ( ( ABI_n /Int 2 ) ==K 0 ) #then 150 #else ( 437 +Int ( ( ( num0(ABI_n) -Int 1 ) *Int 172 ) +Int ( num1(ABI_n) *Int 287 ) ) ) #fi) #else (#if ( ( ABI_n /Int 2 ) ==K 0 ) #then 160 #else ( 447 +Int ( ( num0(ABI_n) *Int 172 ) +Int ( ( num1(ABI_n) -Int 1 ) *Int 287 ) ) ) #fi) #fi) #fi)


if

    // TODO: strengthen
    #sizeWordStack(WS) <= 999
    num0(n) >= 0
    num1(n) >= 0
    b =/= 0
    0 <= #rpow(b, x, n, b)
    #rpow(b, x, n, b) * b < pow256

calls

    Pot.rpow-loop
```

#### accumulating interest

```act
behaviour drip of Pot
interface drip()

for all

    Rho  : uint48
    Chi  : uint256
    Dsr  : uint256
    Pie  : uint256
    Vow  : address
    Vat  : address VatLike
    May  : uint256
    Dai  : uint256
    Sin  : uint256
    Vice : uint256
    Debt : uint256

storage

    rho |-> Rho => TIME
    chi |-> Chi => #rmul(#rpow(#Ray, Dsr, TIME - Rho, #Ray), Chi)
    dsr |-> Dsr
    Pie |-> Pie
    vow |-> Vow
    vat |-> Vat

storage Vat

    wards[ACCT_ID] |-> May
    dai[ACCT_ID]   |-> Dai  => Dai + Pie * (#rmul(#rpow(#Ray, Dsr, TIME - Rho, #Ray), Chi) - Chi)
    sin[Vow]       |-> Sin  => Sin + Pie * (#rmul(#rpow(#Ray, Dsr, TIME - Rho, #Ray), Chi) - Chi)
    vice           |-> Vice => Vice + Pie * (#rmul(#rpow(#Ray, Dsr, TIME - Rho, #Ray), Chi) - Chi)
    debt           |-> Debt => Debt + Pie * (#rmul(#rpow(#Ray, Dsr, TIME - Rho, #Ray), Chi) - Chi)

iff

    May == 1
    VCallValue == 0
    VCallDepth < 1024

gas

    ( ( 5068 + ( ( ( ( ( #if ( ( Dai ==K 0 ) andBool (notBool ( ( Dai + ( Pie * ( ( ( (#rpow( #Ray , Dsr , ( TIME - Rho ) , #Ray )) * Chi ) / #Ray ) - Chi ) ) ) ==K 0 ) ) ) #then 15000 #else 0 #fi) + ( #if ( ( Sin ==K 0 ) andBool (notBool ( ( Sin + ( Pie * ( ( ( (#rpow( #Ray , Dsr , ( TIME - Rho ) , #Ray )) * Chi ) / #Ray ) - Chi ) ) ) ==K 0 ) ) ) #then 15000 #else 0 #fi) ) + ( #if ( ( Vice ==K 0 ) andBool (notBool ( ( Vice + ( Pie * ( ( ( (#rpow( #Ray , Dsr , ( TIME - Rho ) , #Ray )) * Chi ) / #Ray ) - Chi ) ) ) ==K 0 ) ) ) #then 15000 #else 0 #fi) ) + ( #if ( ( Debt ==K 0 ) andBool (notBool ( ( Debt + ( Pie * ( ( ( (#rpow( #Ray , Dsr , ( TIME - Rho ) , #Ray )) * Chi ) / #Ray ) - Chi ) ) ) ==K 0 ) ) ) #then 15000 #else 0 #fi) ) + 26564 ) ) + ( ( ( ( 819 + ( #if ( Dsr ==K 0 ) #then ( #if ( ( TIME - Rho ) ==K 0 ) #then 82 #else 92 #fi) #else ( #if ( ( ( TIME - Rho ) modInt 2 ) ==K 0 ) #then ( #if ( ( ( TIME - Rho ) / 2 ) ==K 0 ) #then 150 #else ( 437 + ( ( ( num0(( TIME - Rho )) - 1 ) * 172 ) + ( num1(( TIME - Rho )) * 287 ) ) ) #fi) #else ( #if ( ( ( TIME - Rho ) / 2 ) ==K 0 ) #then 160 #else ( 447 + ( ( num0(( TIME - Rho )) * 172 ) + ( ( num1(( TIME - Rho )) - 1 ) * 287 ) ) ) #fi) #fi) #fi) ) + ( #if ( Chi ==K 0 ) #then 5946 #else 5998 #fi) ) + ( 5711 + ( #if ( ( Rho ==K 0 ) andBool (notBool ( TIME ==K 0 ) ) ) #then 15000 #else 0 #fi) ) ) + ( #if ( ( ( ( (#rpow( #Ray , Dsr , ( TIME - Rho ) , #Ray )) * Chi ) / #Ray ) - Chi ) ==K 0 ) #then 951 #else 1003 #fi) ) )

if

    num0(TIME - Rho) >= 0
    num1(TIME - Rho) >= 0
    0 <= #rpow(#Ray, Dsr, TIME - Rho, #Ray)
    #rpow(#Ray, Dsr, TIME - Rho, #Ray) * #Ray < pow256

iff in range uint256

    TIME - Rho
    #rpow(#Ray, Dsr, TIME - Rho, #Ray) * Chi
    #rmul(#rpow(#Ray, Dsr, TIME - Rho, #Ray), Chi)
    #rmul(#rpow(#Ray, Dsr, TIME - Rho, #Ray), Chi) - Chi
    Pie * (#rmul(#rpow(#Ray, Dsr, TIME - Rho, #Ray), Chi) - Chi)
    Dai + Pie * (#rmul(#rpow(#Ray, Dsr, TIME - Rho, #Ray), Chi) - Chi)
    Sin + Pie * (#rmul(#rpow(#Ray, Dsr, TIME - Rho, #Ray), Chi) - Chi)
    Vice + Pie * (#rmul(#rpow(#Ray, Dsr, TIME - Rho, #Ray), Chi) - Chi)
    Debt + Pie * (#rmul(#rpow(#Ray, Dsr, TIME - Rho, #Ray), Chi) - Chi)

calls

    Pot.rmul
    Pot.rpow
    Pot.adduu
    Pot.subuu
    Pot.muluu
    Vat.suck
```

#### deposits and withdrawals

```act
behaviour join of Pot
interface join(uint256 wad)

for all

    Pie_u   : uint256
    Pie_tot : uint256
    Chi     : uint256
    Vat     : address VatLike
    Can     : uint256
    Dai_u   : uint256
    Dai_p   : uint256

storage

    pie[CALLER_ID] |-> Pie_u   => Pie_u + wad
    Pie            |-> Pie_tot => Pie_tot + wad
    chi            |-> Chi
    vat            |-> Vat

storage Vat

    can[CALLER_ID][ACCT_ID] |-> Can
    dai[CALLER_ID]          |-> Dai_u => Dai_u - Chi * wad
    dai[ACCT_ID]            |-> Dai_p => Dai_p + Chi * wad

iff

    VCallValue == 0
    VCallDepth < 1024
    Can == 1

iff in range uint256

    Pie_u + wad
    Pie_tot + wad
    Chi * wad
    Dai_u - Chi * wad
    Dai_p + Chi * wad

if
    ACCT_ID =/= CALLER_ID

calls

    Pot.adduu
    Pot.muluu
    Vat.move-diff
```

```act
behaviour exit of Pot
interface exit(uint256 wad)

for all

    Pie_u   : uint256
    Pie_tot : uint256
    Chi     : uint256
    Vat     : address VatLike
    Dai_u   : uint256
    Dai_p   : uint256

storage

    pie[CALLER_ID] |-> Pie_u   => Pie_u - wad
    Pie            |-> Pie_tot => Pie_tot - wad
    chi            |-> Chi
    vat            |-> Vat

storage Vat

    can[ACCT_ID][ACCT_ID] |-> _
    dai[ACCT_ID]          |-> Dai_p => Dai_p - Chi * wad
    dai[CALLER_ID]        |-> Dai_u => Dai_u + Chi * wad

iff

    VCallValue == 0
    VCallDepth < 1024

iff in range uint256

    Pie_u - wad
    Pie_tot - wad
    Chi * wad
    Dai_u + Chi * wad
    Dai_p - Chi * wad

if
    ACCT_ID =/= CALLER_ID

calls

    Pot.subuu
    Pot.muluu
    Vat.move-diff
```
