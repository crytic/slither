// The version pragma below should get flagged by the detector
// Reason: The expression "^0.4.0 >0.4.2" allows old solc (<0.4.23)
pragma solidity ^0.4.24; 
pragma solidity >=0.4.0 <0.6.0;
contract Contract{

}
