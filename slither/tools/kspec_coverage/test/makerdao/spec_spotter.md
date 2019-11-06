```act
behaviour ilks of Spotter
interface ilks(bytes32 ilk)

for all
  Pip : address
  Mat : uint256

storage
  ilks[ilk].pip |-> Pip
  ilks[ilk].mat |-> Mat

iff
  VCallValue == 0

returns Pip : Mat
```
