// SPDX-License-Identifier: Unlicensed

pragma solidity ^0.8.13; 


contract multiplyContract {
 
    int128 a1 ;
    int128 a2 ;
     
    function setFirst(int128 val1) private {
        a1 = val1;
    }
     
    function setSecond(int128 val2) private {
        a2 = val2;
    }
     
    function multiply() view private returns (int128) {
        int128 result = a1 * a2 ;
        return result;
    }
 
}