pragma solidity 0.8.17;

contract CacheArrayLength
{
    struct S
    {
        uint s;
    }

    S[] array;
    S[] array2;
    uint public x;

    function h() external
    {
        
    }

    function g() internal
    {
        this.h();
    }

    function h_view() external view
    {

    }

    function g_view() internal view
    {
        this.h_view();
    }

    function f() public
    {
        // array accessed but length doesn't change
        for (uint i = 0; i < array.length; i++) // warning should appear
        {
            array[i] = S(0);
        }

        // array.length doesn't change, but array.length not used in loop condition
        for (uint i = array.length; i >= 0; i--)
        {

        }

        // array.length changes in the inner loop
        for (uint i = 0; i < array.length; i++)
        {
            for (uint j = i; j < 2 * i; j++)
                array.push(S(j));
        }

        // array.length changes
        for (uint i = 0; i < array.length; i++)
        {
            array.pop();
        }

        // array.length changes
        for (uint i = 0; i < array.length; i++)
        {
            delete array;
        }

        // array.length doesn't change despite using delete
        for (uint i = 0; i < array.length; i++) // warning should appear
        {
            delete array[i];
        }

        // array.length changes; push used in more complex expression
        for (uint i = 0; i < array.length; i++)
        {
            array.push() = S(i);
        }

        // array.length doesn't change
        for (uint i = 0; i < array.length; i++) // warning should appear
        {
            array2.pop();
            array2.push();
            array2.push(S(i));
            delete array2;
            delete array[0];
        }

        // array.length changes; array2.length doesn't change
        for (uint i = 0; i < 7; i++)
        {
            for (uint j = i; j < array.length; j++)
            {
                for (uint k = 0; k < j; k++)
                {

                }

                for (uint k = 0; k < array2.length; k++) // warning should appear
                {
                    array.pop();
                }
            }
        }

        // array.length doesn't change; array2.length changes
        for (uint i = 0; i < 7; i++)
        {
            for (uint j = i; j < array.length; j++) // warning should appear
            {
                for (uint k = 0; k < j; k++)
                {

                }

                for (uint k = 0; k < array2.length; k++)
                {
                    array2.pop();
                }
            }
        }

        // none of array.length and array2.length changes
        for (uint i = 0; i < 7; i++)
        {
            for (uint j = i; j < array.length; j++) // warning should appear
            {
                for (uint k = 0; k < j; k++)
                {

                }

                for (uint k = 0; k < array2.length; k++) // warning should appear
                {
                    
                }
            }
        }

        S[] memory array3;

        // array3 not modified, but it's not a storage array
        for (uint i = 0; i < array3.length; i++)
        {

        }

        // array not modified, but it may potentially change in an internal function call
        for (uint i = 0; i < array.length; i++)
        {
            g();
        }

        // array not modified, but it may potentially change in an external function call
        for (uint i = 0; i < array.length; i++)
        {
            this.h();
        }

        // array not modified and it cannot be changed in a function call since g_view is a view function
        for (uint i = 0; i < array.length; i++) // warning should appear
        {
            g_view();
        }

        // array not modified and it cannot be changed in a function call since h_view is a view function
        for (uint i = 0; i < array.length; i++) // warning should appear
        {
            this.h_view();
        }
        // array not modified and it cannot be changed in a function call since x is a public state variable
        for (uint i = 0; i < array.length; i++) // warning should appear
        {
            this.x();
        }
    }   
}