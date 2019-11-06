```act
behaviour wards of Dai
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
behaviour allowance of Dai
interface allowance(address holder, address spender)

types

    Allowed : uint256

storage

    allowance[holder][spender] |-> Allowed

iff

    VCallValue == 0

returns Allowed
```

```act
behaviour balanceOf of Dai
interface balanceOf(address who)

types

    Balance : uint256

storage

    balanceOf[who] |-> Balance

iff

    VCallValue == 0

returns Balance
```

```act
behaviour totalSupply of Dai
interface totalSupply()

types

    Supply : uint256

storage

    totalSupply |-> Supply

iff

    VCallValue == 0

returns Supply
```

```act
behaviour nonces of Dai
interface nonces(address who)

types

    Nonce : uint256

storage

    nonces[who] |-> Nonce

iff

    VCallValue == 0

returns Nonce
```

```act
behaviour decimals of Dai
interface decimals()

iff

    VCallValue == 0

returns 18
```

```act
behaviour name of Dai
interface name()

iff

    VCallValue == 0

returnsRaw #asByteStackInWidthaux(32, 31, 32, #enc(#string("Dai Stablecoin")))
```

```act
behaviour version of Dai
interface version()

iff

    VCallValue == 0

returnsRaw #asByteStackInWidthaux(32, 31, 32, #enc(#string("1")))
```

```act
behaviour symbol of Dai
interface symbol()

iff

    VCallValue == 0

returnsRaw #asByteStackInWidthaux(32, 31, 32, #enc(#string("DAI")))
```

```act
behaviour PERMIT_TYPEHASH of Dai
interface PERMIT_TYPEHASH()

iff

    VCallValue == 0

returns keccak(#parseByteStackRaw("Permit(address holder,address spender,uint256 nonce,uint256 expiry,bool allowed)"))
```

```act
behaviour DOMAIN_SEPARATOR of Dai
interface DOMAIN_SEPARATOR()

for all

    Dom : uint256

storage

    DOMAIN_SEPARATOR |-> Dom

iff

    VCallValue == 0

returns Dom
```

### Mutators


#### adding and removing owners

Any owner can add and remove owners.

```act
behaviour rely-diff of Dai
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
behaviour rely-same of Dai
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
behaviour deny-diff of Dai
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
behaviour deny-same of Dai
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

```act
behaviour adduu of Dai
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
behaviour subuu of Dai
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
behaviour transfer-diff of Dai
interface transfer(address dst, uint wad)

types

    SrcBal : uint256
    DstBal : uint256

storage

    balanceOf[CALLER_ID] |-> SrcBal => SrcBal - wad
    balanceOf[dst]        |-> DstBal => DstBal + wad

iff in range uint256

    SrcBal - wad
    DstBal + wad

iff

    VCallValue == 0

if
    CALLER_ID =/= dst

returns 1

calls

    Dai.adduu
    Dai.subuu
```

```act
behaviour transfer-same of Dai
interface transfer(address dst, uint wad)

types

    SrcBal : uint256

storage

    balanceOf[CALLER_ID] |-> SrcBal => SrcBal

iff in range uint256

    SrcBal - wad

iff

    VCallValue == 0

if

    CALLER_ID == dst

returns 1

calls

    Dai.adduu
    Dai.subuu
```

```act
behaviour transferFrom-diff of Dai
interface transferFrom(address src, address dst, uint wad)

types

    SrcBal  : uint256
    DstBal  : uint256
    Allowed : uint256

storage

    allowance[src][CALLER_ID] |-> Allowed => #if (src == CALLER_ID or Allowed == maxUInt256) #then Allowed #else Allowed - wad #fi
    balanceOf[src]            |-> SrcBal  => SrcBal  - wad
    balanceOf[dst]            |-> DstBal  => DstBal  + wad

iff in range uint256

    SrcBal - wad
    DstBal + wad

iff
    wad <= Allowed or src == CALLER_ID
    VCallValue == 0

if
    src =/= dst

returns 1

calls

    Dai.adduu
    Dai.subuu
```

```act
behaviour move-diff of Dai
interface move(address src, address dst, uint wad)

types

    SrcBal  : uint256
    DstBal  : uint256
    Allowed : uint256

storage

    allowance[src][CALLER_ID] |-> Allowed => #if (src == CALLER_ID or Allowed == maxUInt256) #then Allowed #else Allowed - wad #fi
    balanceOf[src]            |-> SrcBal  => SrcBal  - wad
    balanceOf[dst]            |-> DstBal  => DstBal  + wad

iff in range uint256

    SrcBal - wad
    DstBal + wad

iff
    wad <= Allowed or src == CALLER_ID
    VCallValue == 0

if
    src =/= dst

calls

    Dai.transferFrom-diff
```

```act
behaviour push of Dai
interface push(address dst, uint wad)

types

    SrcBal  : uint256
    DstBal  : uint256

storage

    balanceOf[CALLER_ID]      |-> SrcBal  => SrcBal  - wad
    balanceOf[dst]            |-> DstBal  => DstBal  + wad

iff in range uint256

    SrcBal - wad
    DstBal + wad

iff
    VCallValue == 0

if
    CALLER_ID =/= dst

calls

    Dai.transferFrom-diff
```

```act
behaviour pull of Dai
interface pull(address src, uint wad)

types

    SrcBal  : uint256
    DstBal  : uint256
    Allowed : uint256

storage

    allowance[src][CALLER_ID] |-> Allowed => #if (src == CALLER_ID or Allowed == maxUInt256) #then Allowed #else Allowed - wad #fi
    balanceOf[src]            |-> SrcBal  => SrcBal  - wad
    balanceOf[CALLER_ID]      |-> DstBal  => DstBal  + wad

iff in range uint256

    SrcBal - wad
    DstBal + wad

iff
    wad <= Allowed or src == CALLER_ID
    VCallValue == 0

if
    src =/= CALLER_ID

calls

    Dai.transferFrom-diff
```

```act
behaviour transferFrom-same of Dai
interface transferFrom(address src, address dst, uint wad)

types

    SrcBal  : uint256
    Allowed : uint256

storage

    allowance[src][CALLER_ID] |-> Allowed => #if (src == CALLER_ID or Allowed == maxUInt256) #then Allowed #else Allowed - wad #fi
    balanceOf[src]            |-> SrcBal  => SrcBal

iff in range uint256

    SrcBal - wad

iff
    wad <= Allowed or src == CALLER_ID
    VCallValue == 0

if
    src == dst

returns 1

calls

    Dai.adduu
    Dai.subuu
```

```act
behaviour mint of Dai
interface mint(address dst, uint wad)

types

    DstBal      : uint256
    TotalSupply : uint256

storage

    wards[CALLER_ID] |-> May
    balanceOf[dst]   |-> DstBal => DstBal + wad
    totalSupply      |-> TotalSupply => TotalSupply + wad

iff in range uint256

    DstBal + wad
    TotalSupply + wad

iff

    May == 1
    VCallValue == 0

calls

    Dai.adduu
```

```act
behaviour burn of Dai
interface burn(address src, uint wad)

types

    SrcBal      : uint256
    TotalSupply : uint256
    Allowed     : uint256

storage

    allowance[src][CALLER_ID] |-> Allowed => #if (src == CALLER_ID or Allowed == maxUInt256) #then Allowed #else Allowed - wad #fi
    balanceOf[src]            |-> SrcBal => SrcBal - wad
    totalSupply               |-> TotalSupply => TotalSupply - wad

iff in range uint256

    SrcBal - wad
    TotalSupply - wad

iff

    (Allowed == maxUInt256) or (wad <= Allowed) or (src == CALLER_ID)
    VCallValue == 0

calls

    Dai.subuu
```


```act
behaviour approve of Dai
interface approve(address usr, uint wad)

types

    Allowed : uint256

storage

    allowance[CALLER_ID][usr] |-> Allowed => wad

iff
    VCallValue == 0

returns 1
```

```act
behaviour permit of Dai
interface permit(address hodler, address ombudsman, uint256 n, uint256 ttl, bool may, uint8 v, bytes32 r, bytes32 s)

types

    Nonce   : uint256
    Allowed : uint256
    Domain_separator : bytes32

storage

    nonces[hodler]               |-> Nonce => 1 + Nonce
    DOMAIN_SEPARATOR             |-> Domain_separator
    allowance[hodler][ombudsman] |-> Allowed => (#if may == 0 #then 0 #else maxUInt256 #fi)

iff

    hodler == #symEcrec(keccakIntList(#asWord(#parseHexWord("0x19") : #parseHexWord("0x1") : .WordStack) Domain_separator keccakIntList(keccak(#parseByteStackRaw("Permit(address holder,address spender,uint256 nonce,uint256 expiry,bool allowed)")) hodler ombudsman n ttl may)), v, r, s)
    ttl == 0 or TIME <= ttl
    VCallValue == 0
    n == Nonce
    VCallDepth < 1024

if

    #rangeUInt(256, Nonce + 1)
```
