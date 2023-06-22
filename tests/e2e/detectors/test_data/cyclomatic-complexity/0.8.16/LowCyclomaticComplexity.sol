pragma solidity 0.8.16;

contract LowCyclomaticComplexity
{
    function lowCC() public pure
    {
        for (uint i = 0; i < 10; i++)
        {
            for (uint j = 0; j < i; j++)
            {
                uint a = i + 1;
            }  
        }
    }
}