# Slither Printers

Slither allows printing contracts information through its printers.

## Quick Summary
`slither.py file.sol --print-quick-summary`

Output a quick summary of the contract.
Example:
```
$ slither vulns/0x01293cd77f68341635814c35299ed30ae212789e.sol --printer-quick-summary
```
<img src="imgs/quick-summary.png" width="300">

## Summary
`slither.py file.sol --print-summary`

Output a summary of the contract showing for each function:
- What are the visibility and the modifiers 
- What are the state variables read or written
- What are the calls

Example:
```
$ slither examples/bugs/backdoor.sol --printer-summary
```
```
[...]

Contract C
Contract vars: []
Inheritances:: []
 
+-----------------+------------+-----------+----------------+-------+---------------------------+----------------+
|     Function    | Visibility | Modifiers |      Read      | Write |       Internal Calls      | External Calls |
+-----------------+------------+-----------+----------------+-------+---------------------------+----------------+
| i_am_a_backdoor |   public   |     []    | ['msg.sender'] |   []  | ['selfdestruct(address)'] |       []       |
+-----------------+------------+-----------+----------------+-------+---------------------------+----------------+

+-----------+------------+------+-------+----------------+----------------+
| Modifiers | Visibility | Read | Write | Internal Calls | External Calls |
+-----------+------------+------+-------+----------------+----------------+
+-----------+------------+------+-------+----------------+----------------+
```

## Inheritance Graph
`slither file.sol --printer-inheritance`

Output a graph showing the inheritance interaction between the contracts.
Example:
```
$ slither examples/DAO.sol --print-inheritance
[...]
INFO:PrinterInheritance:Inheritance Graph: examples/DAO.sol.dot
```

The output format is [dot](https://www.graphviz.org/) and can be converted to svg using:
```
dot examples/DAO.sol.dot -Tsvg -o examples/DAO.svg 
```

Functions in orange override a parent's functions. If a variable points to another contract, the contract type is written in blue.

<img src="imgs/DAO.svg" width="700">


## Variables written and authorization
`slither file.sol --printer-vars-and-auth`

Print the variables written and the check on `msg.sender` of each function.
```
...
INFO:Printers:
Contract MyNewBank
+----------+-------------------------+--------------------------+
| Function | State variables written | Conditions on msg.sender |
+----------+-------------------------+--------------------------+
|   kill   |           []            | ['msg.sender != owner']  |
| withdraw |           []            | ['msg.sender != owner']  |
|   init   |       [u'owner']        |            []            |
|  owned   |       [u'owner']        |            []            |
| fallback |     [u'deposits']       |            []            |
+----------+-------------------------+--------------------------+
```

