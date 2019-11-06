```act
behaviour wards of Jug
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
behaviour ilks of Jug
interface ilks(bytes32 ilk)

for all

    Vow : bytes32
    Duty : uint256
    Rho : uint48

storage

    ilks[ilk].duty |-> Duty
    ilks[ilk].rho  |-> Rho

iff

    VCallValue == 0

returns Duty : Rho
```

#### `vat` address

```act
behaviour vat of Jug
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
behaviour vow of Jug
interface vow()

for all

    Vow : address

storage

    vow |-> Vow

iff

    VCallValue == 0

returns Vow
```

#### global interest rate

```act
behaviour base of Jug
interface base()

for all

    Base : uint256

storage

    base |-> Base

iff

    VCallValue == 0

returns Base
```


### Mutators

#### adding and removing owners

```act
behaviour rely-diff of Jug
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
behaviour rely-same of Jug
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
behaviour deny-diff of Jug
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
behaviour deny-same of Jug
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

#### initialising an `ilk`


```act
behaviour init of Jug
interface init(bytes32 ilk)

for all

    May  : uint256
    Duty : uint256
    Rho  : uint256

storage

    wards[CALLER_ID] |-> May
    ilks[ilk].duty   |-> Duty => #Ray
    ilks[ilk].rho    |-> Rho => TIME

iff

    // act: caller is `. ? : not` authorised
    May == 1
    // act: `Duty` is `. ? : not` zero
    Duty == 0
    VCallValue == 0

```

#### setting `ilk` data


```act
behaviour file of Jug
interface file(bytes32 ilk, bytes32 what, uint256 data)

for all

    May : uint256
    Duty : uint256

storage

    wards[CALLER_ID] |-> May
    ilks[ilk].duty   |-> Duty => (#if what == #string2Word("duty") #then data #else Duty #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0
```

#### setting the base rate

```act
behaviour file-base of Jug
interface file(bytes32 what, uint256 data)

for all

    May  : uint256
    Base : uint256

storage

    wards[CALLER_ID] |-> May
    base             |-> Base => (#if what == #string2Word("base") #then data #else Base #fi)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    VCallValue == 0
```

#### setting the `vow`

```act
behaviour file-vow of Jug
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

#### updating the rates

```act
behaviour drip of Jug
interface drip(bytes32 ilk)

for all

    Vat    : address VatLike
    Base   : uint256
    Vow    : address
    Duty   : uint256
    Rho    : uint48
    May    : uint256
    Rate   : uint256
    Art_i  : uint256
    Dai    : uint256
    Debt   : uint256
    Ilk_spot : uint256
    Ilk_line : uint256
    Ilk_dust : uint256

storage

    vat            |-> Vat
    vow            |-> Vow
    base           |-> Base
    ilks[ilk].duty |-> Duty
    ilks[ilk].rho  |-> Rho => TIME

storage Vat

    live           |-> Live
    wards[ACCT_ID] |-> May
    ilks[ilk].rate |-> Rate => Rate + (#rmul(#rpow(#Ray, Base + Duty, TIME - Rho, #Ray), Rate) - Rate)
    ilks[ilk].Art  |-> Art_i
    ilks[ilk].spot |-> Ilk_spot
    ilks[ilk].line |-> Ilk_line
    ilks[ilk].dust |-> Ilk_dust
    dai[Vow]       |-> Dai  => Dai  + Art_i * (#rmul(#rpow(#Ray, Base + Duty, TIME - Rho, #Ray), Rate) - Rate)
    debt           |-> Debt => Debt + Art_i * (#rmul(#rpow(#Ray, Base + Duty, TIME - Rho, #Ray), Rate) - Rate)

iff

    // act: caller is `. ? : not` authorised
    May == 1
    Live == 1
    // act: call stack is not too big
    VCallDepth < 1024
    VCallValue == 0

iff in range uint256

    Base + Duty
    TIME - Rho
    #rpow(#Ray, Base + Duty, TIME - Rho, #Ray) * Rate
    #rmul(#rpow(#Ray, Base + Duty, TIME - Rho, #Ray), Rate)
    #rmul(#rpow(#Ray, Base + Duty, TIME - Rho, #Ray), Rate) - Rate
    Rate + (#rmul(#rpow(#Ray, Base + Duty, TIME - Rho, #Ray), Rate) - Rate)
    Dai  + Art_i * (#rmul(#rpow(#Ray, Base + Duty, TIME - Rho, #Ray), Rate) - Rate)
    Debt + Art_i * (#rmul(#rpow(#Ray, Base + Duty, TIME - Rho, #Ray), Rate) - Rate)

iff in range int256

    Rate
    Art_i
    #rmul(#rpow(#Ray, Base + Duty, TIME - Rho, #Ray), Rate) - Rate
    Art_i * (#rmul(#rpow(#Ray, Base + Duty, TIME - Rho, #Ray), Rate) - Rate)

gas

    ( ( 6466 + ( #if ( ( Base + Duty ) ==K 0 ) #then ( #if ( ( TIME - Rho ) ==K 0 ) #then 82 #else 92 #fi) #else ( #if ( ( ( TIME - Rho ) modInt 2 ) ==K 0 ) #then ( #if ( ( ( TIME - Rho ) / 2 ) ==K 0 ) #then 150 #else ( 437 + ( ( ( num0(( TIME - Rho )) - 1 ) * 172 ) + ( num1(( TIME - Rho )) * 287 ) ) ) #fi) #else ( #if ( ( ( TIME - Rho ) / 2 ) ==K 0 ) #then 160 #else ( 447 + ( ( num0(( TIME - Rho )) * 172 ) + ( ( num1(( TIME - Rho )) - 1 ) * 287 ) ) ) #fi) #fi) #fi) ) + ( #if ( Rate ==K 0 ) #then ( 33558 + ( #if ( ( Rho ==K 0 ) andBool (notBool ( TIME ==K 0 ) ) ) #then 15000 #else 0 #fi) ) #else ( #if ( ( 0 < ( ( ( (#rpow( #Ray , ( Base + Duty ) , ( TIME - Rho ) , #Ray )) * Rate ) / #Ray ) - Rate ) ) ==K false ) #then ( 33594 + ( #if ( ( Rho ==K 0 ) andBool (notBool ( TIME ==K 0 ) ) ) #then 15000 #else 0 #fi) ) #else ( #if ( ( 0 < ( Art_i * ( ( ( (#rpow( #Ray , ( Base + Duty ) , ( TIME - Rho ) , #Ray )) * Rate ) / #Ray ) - Rate ) ) ) ==K false ) #then ( 33644 + ( #if ( ( Rho ==K 0 ) andBool (notBool ( TIME ==K 0 ) ) ) #then 15000 #else 0 #fi) ) #else ( ( ( ( #if ( ( Dai ==K 0 ) andBool (notBool ( ( Dai + ( Art_i * ( ( ( (#rpow( #Ray , ( Base + Duty ) , ( TIME - Rho ) , #Ray )) * Rate ) / #Ray ) - Rate ) ) ) ==K 0 ) ) ) #then 15000 #else 0 #fi) + ( #if ( ( Debt ==K 0 ) andBool (notBool ( ( Debt + ( Art_i * ( ( ( (#rpow( #Ray , ( Base + Duty ) , ( TIME - Rho ) , #Ray )) * Rate ) / #Ray ) - Rate ) ) ) ==K 0 ) ) ) #then 15000 #else 0 #fi) ) + ( #if ( ( Rho ==K 0 ) andBool (notBool ( TIME ==K 0 ) ) ) #then 15000 #else 0 #fi) ) + 33672 ) #fi) #fi) #fi) )

if

    num0(TIME - Rho) >= 0
    num1(TIME - Rho) >= 0
    0 <= #rpow(#Ray, Base + Duty, TIME - Rho, #Ray)
    #rpow(#Ray, Base + Duty, TIME - Rho, #Ray) * #Ray < pow256

calls

    Jug.adduu
    Jug.rpow
```

## `rpow`

```act
behaviour adduu of Jug
interface add(uint256 x, uint256 y) internal

stack

    y : x : JMPTO : WS => JMPTO : x + y : WS

iff in range uint256

    x + y

if

    // TODO: strengthen
    #sizeWordStack(WS) <= 100
```

This is the coinductive lemma.
```
0.    n % 2 == 0
      case: n >= 2
            n even
      gas: 178

1.    n % 2 == 1
1.0.  n / 2 == 0
      case: n == 1
      terminate loop
      gas: 194

1.1.  n / 2 == 1
      case: n >= 3
            n odd
      coinductive step
      gas: 293


num0 n := "number of 0 in n"
num1 n := "number of 1 in n"

gas = 194 + num0(n) * 178 + num1(n) * 293
```

```act
behaviour rpow-loop of Jug
lemma

//  0a3a => 0a7e
pc

    2618 => 2686

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
behaviour rpow of Jug
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

    Jug.rpow-loop
```
