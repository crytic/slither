pragma solidity ^0.5.8;

contract A {                                                                                                                              

  int[3] intArray; // storage signed integer array
  uint[3] uintArray; // storage unsigned integer array


  /* Signed integer array initializations with literal arrays are vulnerable */
  function bad0() public {
    intArray = [-1, -2, -3];                                                                           
  }

  /* Signed integer array assignments are vulnerable if the base types are different e.g. int256 vs int128 */
  function bad1(int128[3] memory userArray) public {                                                                                          
    intArray = userArray;
  }

  /* Unsigned Int array initializations are not vulnerable */
  function good0() public {                                                                                          
    uintArray = [0, 1, 2];                                                                                                     
  }

  /* Unsigned Int array assignments are not vulnerable */
  function good1(uint[3] memory userArray) public {                                                                                      
    uintArray = userArray;                                                                                                     
  }

  /* Assigning individual array elements are not vulnerable */
  function good2() public {                                                                                          
    intArray[1] = -1;                                                                                                     
  }

  /* Assignment between two signed integer arrays of same base type int256 are not vulnerable */
  function good3(int[3] memory userArray) public {                                                                                        
    intArray = userArray;                                                                                                     
  }

  /* Array literal initialization of in-memory signed integer arrays are not vulnerable */
  function good4() public {
    int8[3] memory memIntArray;
    memIntArray = [-1, -2, -3];
  }

}  
