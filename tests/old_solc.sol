// The version pragma below should get flagged by the detector
// Reason: The expression "^0.4.0 >0.4.2" allows old solc (<0.4.23)
pragma solidity ^0.5.22 || 0.4.23 - 0.4.24 || ^0.4.0 >0.4.2 || ~0.0.0    ^0.5.0 <= 0.5.50 || > 0.7.0;

contract Contract{

}
