// SPDX-License-Identifier: MIT
pragma solidity ^0.6.11;

contract DOSVulnerableContract {
    // Function that contains an infinite loop
    uint i =0;
    function infiniteLoop() external {
        while (true) {
 		i+=1;
 	} 
}
