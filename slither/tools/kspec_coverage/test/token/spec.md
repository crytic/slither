```act
behaviour balanceOf of Token
interface balanceOf(address who)

types

    Balance : uint256

storage

    #Token.balances[who] |-> Balance

iff

    VCallValue == 0

returns Balance
```

```act
behaviour totalSupply of Token
interface totalSupply()

types

    Supply : uint256

storage

    #Token.supply |-> Supply

iff

    VCallValue == 0

returns Supply
```

```act
behaviour transfer of Token
interface transfer(address To, uint Value)

types

    FromBal : uint256
    ToBal   : uint256

storage

    #Token.balances[CALLER_ID] |-> FromBal => FromBal - Value
    #Token.balances[To]        |-> ToBal => ToBal + Value

iff in range uint256

    FromBal - Value
    ToBal + Value

iff

    VCallValue == 0
    CALLER_ID =/= To

if
    CALLER_ID =/= To
```

```act
failure transfer-same of Token
interface transfer(address To, uint Value)

types

    FromBal : uint256

storage

    #Token.balances[CALLER_ID] |-> FromBal => FromBal

iff in range uint256

    FromBal - Value

iff

    VCallValue == 0
    CALLER_ID =/= To

if

    CALLER_ID == To
```
