```act
behaviour tempDelta of ConstantTemp
interface tempDelta(uint256 x)

types

  Temperature : uint256

storage

  0 |-> Temperature => Temperature

iff in range uint256

  Temperature + x

iff

  VCallValue == 0


calls

   ConstantTemp.add
   ConstantTemp.sub
```

We can extract the pc values of internal solidity functions:

```act
behaviour add of ConstantTemp
interface add(uint256 x, uint256 y) internal

stack

   y : x : JUMPTo : WS => JUMPTo : x + y : WS

iff in range uint256

    x + y

if

   #sizeWordStack (WS) <= 1018
```

```act
behaviour sub of ConstantTemp
interface sub(uint256 x, uint256 y) internal

stack

   y : x : JUMPTo : WS => JUMPTo : x - y : WS

iff in range uint256

    x - y

if

   #sizeWordStack (WS) <= 1018
```
