```act
behaviour calling of easyNest
interface raiseTemp(uint256 x)

types

  CALLEE      : address Callee
  Temperature : uint256

storage

  0 |-> CALLEE

storage CALLEE

  0 |-> Temperature => Temperature + x

iff in range uint256

  Temperature + x

iff

  VCallDepth < 1024
  VCallValue == 0

calls

  Callee.tempDelta
```

```act
behaviour tempDelta of Callee
interface tempDelta(uint256 x)

types

  Temperature : uint256

storage

  0 |-> Temperature => Temperature + x

iff in range uint256

  Temperature + x

iff

  VCallValue == 0


calls

   Callee.add
```

We can extract the pc values of internal solidity functions:

```act
behaviour add of Callee
interface add(uint256 x, uint256 y) internal

stack

   x : y : JUMPTo : WS => JUMPTo : x + y : WS

iff in range uint256

    x + y

if

   #sizeWordStack (WS) <= 1018
```
