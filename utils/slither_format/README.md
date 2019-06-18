# Slither-format: Automatic Code Improvements

Slither-format is a Slither utility tool which uses Slither detectors to identify code patterns of concern (w.r.t security, readability and optimisation) and automatically fix those code patterns with suggested changes.

Slither detectors highlight names, context and source-mapping of code constructs which are then used by Slither-format to programmatically locate those constructs in the Solidity files and then replace them with changes based on best practices. Lexical analysis for identification of such constructs is confined to the smallest possible region to avoid conflicts with similarly named constructs (with potentially different types or signatures) in other scopes, functions or contracts within the same file (because of shadowing, overloading etc.).

## Features

* Removes declarations of unused state variables
* Changes the visibility of `public` (explicit or implicit until solc 0.5.0) functions to `external` where possible
* Declares state variables as `constant` where possible
* Removes `pure`/`view`/`constant` attributes of functions when they are incorrectly used
* Replaces old/buggy/too-recent versions of `solc` with either `0.4.25` or `0.5.3` 
* Replaces use of different `solc` versions with either `0.4.25` or `0.5.3`
* Replaces names of various program constructs to adhere to Solidity [naming convention](https://solidity.readthedocs.io/en/v0.4.25/style-guide.html#naming-conventions):
    + Contract names are converted to CapWords in contract definitions and uses
    + Structure names are converted to CapWords in structure declarations and uses
    + Event names are converted to CapWords in event declarations and calls
    + Enum names are converted to CapWords in enum declarations and uses
    + State variables:
        + If constant, are converted to UPPERCASE
        + If private, are converted to mixedCase with underscore
        + If not private, are converted to mixedCase
    + Function names are converted to mixedCase in function definitions and calls
    + Function parameters are converted to CapWords beginning with underscores in parameter declaration and uses
    + Function modifiers are converted to mixedCase in modifier definitions and calls
    
## Usage

Run Slither-format on a single file:
``` 
$ slither-format ./utils/slither_format/tests/test_data/constant.sol
``` 

This produces `constant.sol.format` file which has all the feature replacements.

## Dependencies

Slither-format requires Slither and all its dependencies

## Known Limitations

* Naming convention formatting on parameter uses does not work for NatSpec @param attributes
* Naming convention formatting on parameter uses does not work for variables used as indices on LHS (e.g. `_to` in `balances[_to] = 100`)

## Developer Testing

``` 
$ python3 ./slither_format/tests/test_unused_state_vars.py
$ python3 ./slither_format/tests/test_external_function.py
$ python3 ./slither_format/tests/test_constable_states.py
$ python3 ./slither_format/tests/test_constant_function.py
$ python3 ./slither_format/tests/test_solc_version.py
$ python3 ./slither_format/tests/test_pragma.py
$ python3 ./slither_format/tests/test_naming_convention.py
$ python3 ./slither_format/tests/run_all_tests.py
``` 
