pragma solidity 0.8.16;

type aliasTopLevel is uint;

contract C
{
    type aliasContractLevel is uint;
}

contract Test
{
    aliasTopLevel a;
    C.aliasContractLevel b;
}

function f(aliasTopLevel, C.aliasContractLevel)
{

}