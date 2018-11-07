pragma solidity ^0.4.24;

contract BaseContract1{
}

contract BaseContract2{
}

contract ChildContract1 is BaseContract1{
}

contract ChildContract2 is BaseContract1, BaseContract2{
}

contract GrandchildContract1 is ChildContract1{
}