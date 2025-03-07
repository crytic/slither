# SlithIR

Slither translates Solidity an intermediate representation, SlithIR, to enable high-precision analysis via a simple API. It supports taint and value tracking to enable detection of complex patterns.

SlithIR is a work in progress, although it is usable today. New developments in SlithIR are driven by needs identified by new detector modules. Please help us bugtest and enhance SlithIR!

## What is an IR?

In language design, compilers often operate on an “intermediate representation” (IR) of a language that carries extra details about the program as it is parsed. For example, a compiler creates a parse tree of a program that represents a program as written. However, the compiler can continue to enrich this tree with information, such as taint information, source location, and other items that could have impacted an item from control flow. Additionally, languages such as Solidity have inheritance, meaning that functions and methods may be defined outside the scope of a given contract. An IR could linearize these methods, allowing additional transformations and processing of the contract’s source code.

A demonstrative example would be LLVM’s IR vs C or x86 code. While C will clearly demonstrate a function call, it may be missing details about the underlying system, the path to a location, and so on. Likewise, while an analog to the same call would be clear in x86, this would lose all transient details of which variables and which path an application had taken to arrive at a specific call. LLVM’s IR solves this by abstracting away the specific details of a call instruction, while still capturing the variables, environmental state, and other values that lead to this position. In this way, LLVM can perform additional introspection of the resulting code, and use these analyses to drive other optimizations or information to other passes of the compiler.

## Why does Slither translate to an IR?

Solidity is a quirky language with a number of edge cases, both in terms of syntax and semantics. By translating to an IR, Slither normalizes many of these quirks to better analyze the contract. For example, Solidity’s grammar defines an array push as a function call to the array. A straightforward representation of this semantic would be indistinguishable from a normal function call. Slither, in contrast, treats array pushes as a specific operation, allowing further analysis of the accesses to arrays and their impact to the security of a program. Moreover, the operators in SlithIR have a hierarchy, so, for example in a few lines of code you can track all the operators that write to a variable, which makes it trivial to write precise taint analysis.

Additionally, Slither can include non-trivial variable tracking by default by translating to an IR. This can build richer representations of contracts and allow for deeper analysis of potential vulnerabilities. For example, answering the question “can a user control a variable” is central to uncovering more complex vulnerabilities from a static position. Slither will propagate information from function parameters to program state in an iterative fashion, which captures the control flow of information across potentially multiple transactions. In this way, Slither can enrich information and statically provide a large amount of assurance to contracts that standard vulnerabilities exist and are reachable under certain conditions.

## Example

`$ slither file.sol --print slithir` will output the IR for every function.

```
$ slither examples/printers/slihtir.sol --printers slithir
Contract UnsafeMath
	Function add(uint256,uint256)
		Expression: a + b
		IRs:
			TMP_0(uint256) = a + b
			RETURN TMP_0
	Function min(uint256,uint256)
		Expression: a - b
		IRs:
			TMP_0(uint256) = a - b
			RETURN TMP_0
Contract MyContract
	Function transfer(address,uint256)
		Expression: balances[msg.sender] = balances[msg.sender].min(val)
		IRs:
			REF_3(uint256) -> balances[msg.sender]
			REF_1(uint256) -> balances[msg.sender]
			TMP_1(uint256) = LIBRARY_CALL, dest:UnsafeMath, function:min, arguments:['REF_1', 'val']
			REF_3 := TMP_1
		Expression: balances[to] = balances[to].add(val)
		IRs:
			REF_3(uint256) -> balances[to]
			REF_1(uint256) -> balances[to]
			TMP_1(uint256) = LIBRARY_CALL, dest:UnsafeMath, function:add, arguments:['REF_1', 'val']
			REF_3 := TMP_1
```

# SlithIR Specification

## Variables

- `StateVariable`
- `LocalVariable`
- `Constant` (`string` or `int`)
- `SolidityVariable`
- `TupleVariable`
- `TemporaryVariable` (variables added by SlithIR)
- `ReferenceVariable` (variables added by SlithIR, for mapping/index accesses)

In the following we use:

- `LVALUE` can be: `StateVariable`, `LocalVariable`, `TemporaryVariable`, `ReferenceVariable` or `TupleVariable`
- `RVALUE` can be: `StateVariable`, `LocalVariable`, `Constant`, `SolidityVariable`, `TemporaryVariable` or `ReferenceVariable`

## Operators

- All the operators inherit from `Operation` and have a `read` attribute returning the list of variables read (see [slither/slithir/operations/operation.py](https://github.com/crytic/slither/blob/master/slither/slithir/operations/operation.py)).
- All the operators writing to a `LVALUE` inherit from `OperationWithLValue` and have the `lvalue` attribute (see [slither/slithir/operations/lvalue.py](https://github.com/crytic/slither/blob/master/slither/slithir/operations/lvalue.py)).

### Assignment

- `LVALUE := RVALUE`
- `LVALUE := Tuple`
- `LVALUE := Function` (for dynamic function)

### Binary Operation

- `LVALUE = RVALUE ** RVALUE`
- `LVALUE = RVALUE * RVALUE`
- `LVALUE = RVALUE / RVALUE`
- `LVALUE = RVALUE % RVALUE`
- `LVALUE = RVALUE + RVALUE`
- `LVALUE = RVALUE - RVALUE`
- `LVALUE = RVALUE << RVALUE`
- `LVALUE = RVALUE >> RVALUE`
- `LVALUE = RVALUE & RVALUE`
- `LVALUE = RVALUE ^ RVALUE`
- `LVALUE = RVALUE | RVALUE`
- `LVALUE = RVALUE < RVALUE`
- `LVALUE = RVALUE > RVALUE`
- `LVALUE = RVALUE <= RVALUE`
- `LVALUE = RVALUE >= RVALUE`
- `LVALUE = RVALUE == RVALUE`
- `LVALUE = RVALUE != RVALUE`
- `LVALUE = RVALUE && RVALUE`
- `LVALUE = RVALUE -- RVALUE`

### Unary Operation

- `LVALUE = ! RVALUE`
- `LVALUE = ~ RVALUE`

### Index

- `REFERENCE -> LVALUE [ RVALUE ]`

Note: The reference points to the memory location

### Member

- `REFERENCE -> LVALUE . RVALUE`
- `REFERENCE -> CONTRACT . RVALUE`
- `REFERENCE -> ENUM . RVALUE`

Note: The reference points to the memory location

### New Operators

- `LVALUE = NEW_ARRAY ARRAY_TYPE DEPTH(:int)`

`ARRAY_TYPE` is a [solidity_types](https://github.com/crytic/slither/tree/master/slither/core/solidity_types)

`DEPTH` is used for arrays of multiple dimensions.

- `LVALUE = NEW_CONTRACT CONSTANT`
- `LVALUE = NEW_STRUCTURE STRUCTURE`
- `LVALUE = NEW_ELEMENTARY_TYPE ELEMENTARY_TYPE`

`ELEMENTARY_TYPE` is defined in [slither/core/solidity_types/elementary_type.py](https://github.com/crytic/slither/blob/master/slither/core/solidity_types/elementary_type.py)

### Push Operator

- `PUSH LVALUE RVALUE`
- `PUSH LVALUE Function` (for dynamic function)

### Delete Operator

- `DELETE LVALUE`

### Conversion

- `CONVERT LVALUE RVALUE TYPE`

TYPE is a [solidity_types](https://github.com/crytic/slither/tree/master/slither/core/solidity_types)

### Unpack

- `LVALUE = UNPACK TUPLEVARIABLE INDEX(:int)`

### Array Initialization

- `LVALUE = INIT_VALUES`

`INIT_VALUES` is a list of `RVALUE`, or a list of lists in case of a multidimensional array.

### Calls Operators

In the following, `ARG` is a variable as defined in [SlithIR#variables](https://github.com/crytic/slither/wiki/SlithIR#variables)

- `LVALUE = HIGH_LEVEL_CALL DESTINATION FUNCTION [ARG, ..]`
- `LVALUE = LOW_LEVEL_CALL DESTINATION FUNCTION_NAME [ARG, ..]`

`FUNCTION_NAME` can only be `call`/`delegatecall`/`codecall`

- `LVALUE = SOLIDITY_CALL SOLIDITY_FUNCTION [ARG, ..]`

`SOLIDITY_FUNCTION` is defined in [slither/core/declarations/solidity_variables.py](https://github.com/crytic/slither/blob/master/slither/core/declarations/solidity_variables.py)

- `LVALUE = INTERNAL_CALL FUNCTION [ARG, ..]`
- `LVALUE = INTERNAL_DYNAMIC_CALL FUNCTION_TYPE [ARG, ..]`

`INTERNAL_DYNAMIC_CALL` represents the pointer of function.

`FUNCTION_TYPE` is defined in [slither/core/solidity_types/function_type.py](https://github.com/crytic/slither/blob/master/slither/core/solidity_types/function_type.py)

- `LVALUE = LIBRARY_CALL DESTINATION FUNCTION_NAME [ARG, ..]`
- `LVALUE = EVENT_CALL EVENT_NAME [ARG, ..]`
- `LVALUE = SEND DESTINATION VALUE`
- `TRANSFER DESTINATION VALUE`

Optional arguments:

- `GAS` and `VALUE` for `HIGH_LEVEL_CALL` / `LOW_LEVEL_CALL`.

### Return

- `RETURN RVALUE`
- `RETURN TUPLE`
- `RETURN None`

`Return None` represents an empty return statement.

### Condition

- `CONDITION RVALUE`

`CONDITION` holds the condition in a conditional node.
