contract A {
    error E(A a);

    function f() payable external {
      g();
    }
    
    function g() private {
      bool something = h();

      revert E(this);
    }

    function h() private returns (bool something) {
    }
}


interface I {
  enum Enum { ONE, TWO, THREE }
  error SomethingSomething(Enum e);
}

// abstract contract A2 is I {
// }

// contract B is A2 {
  
//   function f() external {
//     revert SomethingSomething(Enum.ONE);
//   }
// }
//{'argumentTypes': [{'typeIdentifier': 't_contract$_A_$32', 'typeString': 'contract A'}], 'id': 20, 'name': 'E', 'nodeType': 'Identifier', 'overloadedDeclarations': [], 'referencedDeclaration': 5, 'src': '159:1:0', 'typeDescriptions': {'typeIdentifier': 't_function_error_pure$_t_contract$_A_$32_$returns$__$', 'typeString': 'function (contract A) pure'}}
//{'id': 22, 'name': 'this', 'nodeType': 'Identifier', 'overloadedDeclarations': [], 'referencedDeclaration': -28, 'src': '175:4:0', 'typeDescriptions': {'typeIdentifier': 't_contract$_A_$34', 'typeString': 'contract A'}}

