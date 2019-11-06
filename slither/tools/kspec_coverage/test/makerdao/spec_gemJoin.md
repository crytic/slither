```act
behaviour vat of GemJoin
interface vat()

for all

    Vat : address VatLike

storage

    vat |-> Vat

iff

    VCallValue == 0

returns Vat
```

#### the associated `ilk`

```act
behaviour ilk of GemJoin
interface ilk()

for all

    Ilk : bytes32

storage

    ilk |-> Ilk

iff

    VCallValue == 0

returns Ilk
```

#### gem address

```act
behaviour gem of GemJoin
interface gem()

for all

    Gem : address

storage

    gem |-> Gem

iff

    VCallValue == 0

returns Gem
```

### Mutators

#### depositing into the system

```act
behaviour join of GemJoin
interface join(address usr, uint256 wad)

for all

    Vat         : address VatLike
    Ilk         : bytes32
    DSToken     : address DSToken
    May         : uint256
    Vat_bal     : uint256
    Bal_usr     : uint256
    Bal_adapter : uint256
    Owner       : address
    Stopped     : bool
    Allowed     : uint256

storage

    vat |-> Vat
    ilk |-> Ilk
    gem |-> DSToken

storage Vat

    wards[ACCT_ID]      |-> May
    gem[Ilk][usr]       |-> Vat_bal => Vat_bal + wad

storage DSToken

    allowance[CALLER_ID][ACCT_ID] |-> Allowed => #if Allowed == maxUInt256 #then Allowed #else Allowed - wad #fi
    balances[CALLER_ID] |-> Bal_usr     => Bal_usr     - wad
    balances[ACCT_ID]   |-> Bal_adapter => Bal_adapter + wad
    owner_stopped       |-> #WordPackAddrUInt8(Owner, Stopped)

iff

    VCallDepth < 1024
    VCallValue == 0
    wad <= Allowed
    Stopped == 0
    May == 1
    wad <= maxSInt256

iff in range uint256

    Vat_bal + wad
    Bal_usr     - wad
    Bal_adapter + wad

if

    CALLER_ID =/= ACCT_ID

calls

  Vat.slip
  DSToken.transferFrom
```

#### withdrawing from the system

```act
behaviour exit of GemJoin
interface exit(address usr, uint256 wad)

for all

    Vat         : address VatLike
    Ilk         : bytes32
    DSToken     : address DSToken
    May         : uint256
    Wad         : uint256
    Bal_usr     : uint256
    Bal_adapter : uint256
    Owner       : address
    Stopped     : bool

storage

    vat |-> Vat
    ilk |-> Ilk
    gem |-> DSToken

storage Vat

    wards[ACCT_ID]      |-> May
    gem[Ilk][CALLER_ID] |-> Wad => Wad - wad

storage DSToken

    balances[ACCT_ID]   |-> Bal_adapter => Bal_adapter - wad
    balances[usr]       |-> Bal_usr     => Bal_usr     + wad
    owner_stopped       |-> #WordPackAddrUInt8(Owner, Stopped)

iff

    VCallValue == 0
    VCallDepth < 1024
    Stopped == 0
    May == 1
    wad <= posMinSInt256

iff in range uint256

    Wad         - wad
    Bal_adapter - wad
    Bal_usr     + wad

if

    ACCT_ID =/= usr

calls
  Vat.slip
  DSToken.transfer
```
