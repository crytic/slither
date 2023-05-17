contract ABIencodePacked{

  uint a;
  string str1 = "a";
  string str2 = "bc";
  bytes _bytes = "hello world";
  uint[] arr;
  uint[2] arr2;
  string[3] str_arr3; /* This nested dynamic type is not supported in abi.encodePacked mode by solc */
  string[] str_array; /* This nested dynamic type is not supported in abi.encodePacked mode by solc */
  bytes[] bytes_array; /* This nested dynamic type and tuples are not supported in abi.encodePacked mode by solc */

  /* Two dynamic types */
  function bad0(string calldata stra, string calldata strb) external{
    bytes memory packed = abi.encodePacked(stra, strb);
  }

  /* Two dynamic types */
  function bad1(string calldata stra, bytes calldata bytesa) external{
    bytes memory packed = abi.encodePacked(stra, bytesa);
  }

  /* Two dynamic types */
  function bad2(string calldata stra, uint[] calldata arra) external{
    bytes memory packed = abi.encodePacked(stra, arra);
  }

  /* Two dynamic types */
  function bad3_get_hash_for_signature(string calldata name, string calldata doc) external returns (bytes32) {                              
        return keccak256(abi.encodePacked(name, doc));
  }

  /* Two dynamic types between non dynamic types */
  function bad4(bytes calldata a2, bytes calldata a3) external {
    bytes memory packed = abi.encodePacked(a, a2, a3, a);
  }

  /* Two dynamic types but static values*/
  function good0() external{
    bytes memory packed = abi.encodePacked(str1, str2);
  }

  /* Two dynamic types but static values*/
  function good1() external{
    bytes memory packed = abi.encodePacked(str1, _bytes);
  }

  /* Two dynamic types but static values*/
  function good2() external{
    bytes memory packed = abi.encodePacked(str1, arr);
  }
  
  /* No dynamic types */
  function good3() external{
    bytes memory packed = abi.encodePacked(a);
  }

  /* One dynamic type */
  function good4() external{
    bytes memory packed = abi.encodePacked(str1);
  }

  /* One dynamic type */
  function good5() external{
    bytes memory packed = abi.encodePacked(a, str1);
  }

  /* One dynamic type */
  function good6() external{
    bytes memory packed = abi.encodePacked(str1, arr2);
  }

  /* Two dynamic types but not consecutive*/
  function good7(string calldata a, uint b, string calldata c) external{
    bytes memory packed = abi.encodePacked(a, b, c);
  }
}

