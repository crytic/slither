# spec

```act
behaviour add of SafeAdd
interface add(uint256 X, uint256 Y)

iff in range uint256

    X + Y

iff

    VCallValue == 0

returns X + Y
```
```act
behaviour addv2 of SafeAdd
interface addv2(uint256 X, uint256 Y)

iff in range uint256

    X + Y

iff

    VCallValue == 0

returns X + Y
```
