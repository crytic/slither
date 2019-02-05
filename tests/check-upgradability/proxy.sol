/*
   Fake proxy, do not use
*/

pragma solidity ^0.5.0;

contract Proxy{

    address destination;

    function myFunc() public{}

    function () external{
        uint size_destination_code;
        assembly{
            size_destination_code := extcodesize(destination_slot)
        }
        require(size_destination_code>0);
        (bool ret_status,bytes memory ret_values) = destination.delegatecall(msg.data);
        require(ret_status);
        uint length = ret_values.length;
        assembly{
            return (ret_values, length)
        }
    }

}
