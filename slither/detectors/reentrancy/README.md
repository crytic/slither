# Solidity Contract Reentrancy Vulnerabilities Detectors

This category includes detectors that are designed to identify specific vulnerabilities related to the reentrancy in smart contracts written in the Solidity programming language. 
These detectors check for the benign reentrancy bug, report only reentrancy that acts as a double call, don't report reentrancy that doesn't involve Ether, report reentrancy that leads to out-of-order events, report reentrancy that is based on transfer or send and also tokens that allow arbitrary external call on transfer/transfer (such as ERC223/ERC777) that can be exploited through a reentrancy. It helps in identifying potential reentrancy vulnerabilities and assist in adhering to best practices for secure smart contract development.
