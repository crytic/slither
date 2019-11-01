Mainly using this to try some complicated gas stuff
```act
behaviour heal of Vat
interface heal(int256 rad)

for all

    Dai_v : uint256
    Sin_u : uint256
    Debt  : uint256
    Vice  : uint256

storage

    dai[CALLER_ID]   |-> Dai_v => Dai_v - rad
    sin[CALLER_ID]   |-> Sin_u => Sin_u - rad
    debt             |-> Debt  => Debt  - rad
    vice             |-> Vice  => Vice  - rad

iff

    // act: caller is `. ? : not` authorised
    VCallValue == 0

iff in range uint256

    Dai_v - rad
    Sin_u - rad
    Debt  - rad
    Vice  - rad

calls

    Vat.subui
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


