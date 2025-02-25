`slither-find-paths` finds all the paths that reach a given target.

## Usage
```
slither-find-paths file.sol [contract.function targets]
```
- `[contract.function targets]` is either one target, or a list of target

## Example
Tested on [tests/possible_paths/paths.sol](https://github.com/trailofbits/slither/blob/master/tests/possible_paths/paths.sol)
```
$ slither-find-paths paths.sol A.destination
Target functions:
- A.destination()


The following functions reach the specified targets:
- A.call()
- B.call2(A)


The following paths reach the specified targets:
A.call() -> A.destination()

B.call2(A) -> A.call() -> A.destination()
```