pragma solidity 0.8.16;

contract HighCyclomaticComplexity
{
    bool bool1;
    bool bool2;
    bool bool3;
    bool bool4;
    bool bool5;
    bool bool6;
    bool bool7;
    bool bool8;
    bool bool9;
    bool bool10;
    bool bool11;

    function highCC() internal view
    {
        if (bool1)
            if (bool2)
                if (bool3)
                    if (bool4)
                        if (bool5)
                            if (bool6)
                                if (bool7)
                                    if (bool8)
                                        if (bool9)
                                            if (bool10)
                                                if (bool11)
                                                    revert();
    }
}