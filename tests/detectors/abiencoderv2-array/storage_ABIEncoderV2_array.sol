pragma experimental ABIEncoderV2;

contract A {                                                                                                                              

  struct S {
    uint i;
  }
  
  uint[2][3] bad_arr = [[1, 2], [3, 4], [5, 6]];
  uint[3] good_arr = [1, 2, 3];
  S[3] s;
  
  event event1_bad(uint[2][3] bad_arr);
  event event1_good(uint[3] good_arr);
  event event2_bad(S[3] s); 

  function bad0_external(uint [2][3] arr1) external {
  }

  /* Array of arrays passed to an external function is vulnerable */
  function bad0() public {
    this.bad0_external(bad_arr);
  }

  function bad1_external (S[3] s1) external {
  }

  /* Array of structs passed to an external function is vulnerable */
  function bad1 (S[3] s1) public {
    this.bad1_external(s);
  }

  /* Array of arrays passed to abi.encode is vulnerable */
  function bad2() public {                                                                                          
    bytes memory b = abi.encode(bad_arr);
  }

  /* Array of structs passed to abi.encode is vulnerable */
  function bad3() public {                                                                                          
    bytes memory b = abi.encode(s);
  }

  /* Array of arrays passed to an event emit is vulnerable */
  function bad4() public {                                                                                          
    emit event1_bad(bad_arr);
  }

  /* Array of structs passed to an event emit is vulnerable */
  function bad5() public {                                                                                          
    emit event2_bad(s);
  }

  function good0_public (uint[2][3] arr1) public {
  }

  /* Array of arrays passed to a public function is benign */
  function good0() public {
    good0_public(bad_arr);
  }

  function good1_public (S[3] s1) public {
  }

  /* Array of structs passed to a public function is benign */
  function good1 (S[3] s1) {
    good1_public(s);
  }

  /* Array of arrays in-memory passed to abi.encode is benign */
  function good2() public {
    uint8 [2][3] memory bad_arr_mem = [[1, 2], [3, 4], [5, 6]];
    bytes memory b = abi.encode(bad_arr_mem);
  }

  /* Array of structs in-memory passed to abi.encode is benign */
  function good3() public {
    S[3] memory s_mem;
    bytes memory b = abi.encode(s_mem);
  }

  function good4_external(uint[3] arr1) external {
  }

  /* Array of elementary types passed to external function is benign */
  function good4() public {
    this.good4_external(good_arr);
  }

  /* Array of elementary types passed to abi.encode is benign */
  function good5() public {                                                                                          
    bytes memory b = abi.encode(good_arr);
  }

  /* Array of elementary types passed to event emit is benign */
  function good6() public {                                                                                          
    emit event1_good(good_arr);
  }

}  
