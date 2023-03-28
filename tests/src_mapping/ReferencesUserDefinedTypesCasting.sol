pragma solidity 0.8.16;

interface A
{
    function a() external;
}

contract C
{
    function g(address _address) private
    {
        A(_address).a();
    }
}

function f(address _address)
{
    A(_address).a();
}