# Slither Trophies
The following lists security vulnerabilities that were found by Slither. If you found a security vulnerability using Slither, please submit a PR with the relevant information.


## October 2018
- [Basis](https://github.com/trailofbits/publications/blob/master/reviews/basis.pdf)
  - Missing return value check
## November 2018
-  [Origin protocol](https://github.com/trailofbits/publications/blob/master/reviews/origin.pdf)
   - Reentrancy
## July 2019
- [Numerai](https://github.com/trailofbits/publications/blob/master/reviews/numerai.pdf)
  - Deletion of a mapping with structure
  - Missing return value
## September 2019
- [Flexa](https://github.com/trailofbits/publications/blob/master/reviews/Flexa.pdf)
  - Reentrancy (events out of order)
## October 2019
- [0x](https://github.com/trailofbits/publications/blob/master/reviews/0x-protocol.pdf)
  - Missing return value
## December 2019
- [Token mint](https://certificate.quantstamp.com/full/token-mint)
  - Reentrancies
## February 2020
- [Airswap](https://certificate.quantstamp.com/full/airswap)
  - Missing return value check
## March 202
- [Stake Technologies Lockdrop](https://certificate.quantstamp.com/full/stake-technologies-lockdrop)
  - Dangerous strict equality
## May 2020
- [E&Y’s Nightfall](https://blog.trailofbits.com/2020/05/15/bug-hunting-with-crytic/)
  - Missing return value
  - Empty return value
- [DefiStrategies](https://blog.trailofbits.com/2020/05/15/bug-hunting-with-crytic/)
  - Modifier can return the default value
  - Dangerous strict equality allows the contract to be trapped
- [DOSnetwork](https://blog.trailofbits.com/2020/05/15/bug-hunting-with-crytic/)
  - Abi `encodedPacked `collision
- [EthKids](https://blog.trailofbits.com/2020/05/15/bug-hunting-with-crytic/)
  - `msg.value` is used two times to compute a price
- [HQ20](https://blog.trailofbits.com/2020/05/15/bug-hunting-with-crytic/)
  - Reentrancy
## June 2020
- [88mph](https://certificate.quantstamp.com/full/88-mph)
  - Dangerous `block.timestamp` usage
- [Dloop](https://certificate.quantstamp.com/full/dloop-art-registry-smart-contract)
  - Dangerous `block.timestamp` usage
## July 2020
- [Atomic Loans](https://certificate.quantstamp.com/full/atomic-loans)
  - Uninitialized state variable
  - State variable shadowing
  - Reentrancy
- [Parity](https://github.com/trailofbits/publications/blob/master/reviews/parity.pdf)
  - Incorrect constructor name
  - Deletion of a mapping with structure
  - Uninitialized state variables
## August 3 2020
- [Amp](https://github.com/trailofbits/publications/blob/master/reviews/amp.pdf)
  - Duplicate contract name
- [PerlinXRewards](https://certificate.quantstamp.com/full/perlin-x-rewards-sol)
  - Multiple reentrancies
## November 2020
- [Linkswap](https://certificate.quantstamp.com/full/linkswap)
  - Lack of return value check
  - Uninitialized state variable
- [Cryptex](https://certificate.quantstamp.com/full/cryptex)
  - Lack of return value check
- [Unoswap](https://www.unos.finance/wp-content/uploads/2020/11/block-audit.pdf)
  - Contract locking ethers
## December 2020
- [Idle](https://certificate.quantstamp.com/full/idle-finance)
  - Dangerous divide before multiply operations
- [RariCapital](https://certificate.quantstamp.com/full/rari-capital)
  - Lack of return value check
  - Uninitialized state variable
- [wfil-factory](https://github.com/wfil/wfil-factory/commit/a43c1ddf52cf1191ccf1e71a637df02d78b98cc0)
  - Reentrancy
## January 2021
- [Origin Dollar](https://github.com/trailofbits/publications/blob/master/reviews/OriginDollar.pdf) 
  - Reentrancy
  - Variable shadowing
- [OriginTrait](https://github.com/OriginTrail/starfleet-boarding-contract/commit/6481b12abc3cfd0d782abd0e32eabd103d8f6953)
  - Reentrancy


