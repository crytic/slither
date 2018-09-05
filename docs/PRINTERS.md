# Slither Printers

Slither allows printing contracts information through its printers.

## Quick Summary
`slither.py file.sol --print-quick-summary`

Output a quick summary of the contract.
Example:
```
$ slither.py vulns/0x01293cd77f68341635814c35299ed30ae212789e.sol --print-quick-summary
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
$ slither.py vulns/0x01293cd77f68341635814c35299ed30ae212789e.sol --print-summary
```
```
[...]

INFO:Slither:Contract NBACrypto
Contract vars: [u'ceoAddress', u'cfoAddress', u'teams', u'players', u'teamsAreInitiated', u'playersAreInitiated', u'isPaused']
+--------------------+------------+--------------+------------------------+---------------+----------------------------------------------+
|      Function      | Visibility |  Modifiers   |          Read          |     Write     |                    Calls                     |
+--------------------+------------+--------------+------------------------+---------------+----------------------------------------------+
|     pauseGame      |   public   | [u'onlyCeo'] |           []           | [u'isPaused'] |                      []                      |
|    unPauseGame     |   public   | [u'onlyCeo'] |           []           | [u'isPaused'] |                      []                      |
|    GetIsPauded     |   public   |      []      |     [u'isPaused']      |       []      |                      []                      |
|  purchaseCountry   |   public   |      []      |     [u'isPaused']      |   [u'teams']  |       [u'cfoAddress.transfer', u'mul']       |
|                    |            |              |                        |               | [u'require', u'teams.ownerAddress.transfer'] |
|   purchasePlayer   |   public   |      []      |     [u'isPaused']      |  [u'players'] |       [u'cfoAddress.transfer', u'mul']       |
|                    |            |              |                        |               | [u'require', u'teams.ownerAddress.transfer'] |
|                    |            |              |                        |               |      [u'players.ownerAddress.transfer']      |
| modifyPriceCountry |   public   |      []      |           []           |   [u'teams']  |                 [u'require']                 |
|      getTeam       |   public   |      []      |       [u'teams']       |       []      |                      []                      |
|     getPlayer      |   public   |      []      |      [u'players']      |       []      |                      []                      |
|    getTeamPrice    |   public   |      []      |           []           |       []      |                      []                      |
|   getPlayerPrice   |   public   |      []      |           []           |       []      |                      []                      |
|    getTeamOwner    |   public   |      []      |           []           |       []      |                      []                      |
|   getPlayerOwner   |   public   |      []      |           []           |       []      |                      []                      |
|        mul         |  internal  |      []      |           []           |       []      |                 [u'assert']                  |
|        div         |  internal  |      []      |           []           |       []      |                      []                      |
|   InitiateTeams    |   public   | [u'onlyCeo'] | [u'teamsAreInitiated'] |       []      |         [u'require', u'teams.push']          |
|     addPlayer      |   public   | [u'onlyCeo'] |           []           |       []      |              [u'players.push']               |
+--------------------+------------+--------------+------------------------+---------------+----------------------------------------------+
```

## Inheritance Graph
`slither.py file.sol --print-inheritance`

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



