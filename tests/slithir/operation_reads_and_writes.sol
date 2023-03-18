
contract Placeholder {
    constructor() payable {}
    function callMe(uint x) external payable returns (uint) {
        return x;
    }
}

contract NewContractReadAll {
    bytes32 stateVar;

    function readAllStateVariables() external {
        new Placeholder{salt: stateVar} ();
    }

    function readAllLocalVariables() external {
        bytes32 localVar = bytes32(0);
        new Placeholder{salt: localVar} ();
    }


}

contract NewContractWriteAll {
    Placeholder stateVar;
    function writeAllStateVariables() external {
        stateVar = new Placeholder();
    }

    function writeAllLocalVariables() external {
        Placeholder localVar = new Placeholder();
    }
}

contract AssignmentReadAll {
    bytes32 stateVar;

    function readAllStateVariables() external {
        stateVar = stateVar;
    }

    function readAllLocalVariables() external {
        bytes32 localVar;
        stateVar = localVar;
    }

}

contract AssignmentWriteAll {
    bytes32 stateVar;

    function writeAllStateVariables() external {
        stateVar = stateVar;
    }

    function writeAllLocalVariables() external {
        bytes32 localVar = bytes32(0);
    }

}

contract BinaryReadAll {
    uint stateVar1;
    uint stateVar2;

    function readAllStateVariables() external {
        uint localVar = stateVar1 + stateVar2;
    }

    function readAllLocalVariables() external {
        uint localVar1;
        uint localVar2;
        stateVar1 = localVar1 + localVar2;
    }

}

contract BinaryWriteAll {
    uint stateVar;

    function writeAllStateVariables() external {
        stateVar = stateVar + stateVar;
    }

    function writeAllLocalVariables() external {
        uint localVar = stateVar + stateVar;
    }

}

contract HighLevelCallReadAll {
    uint msgValue;
    uint callGas;
    Placeholder destination;
    uint argument;

    function readAllStateVariables() external {
        destination.callMe{value: msgValue, gas: callGas}(argument);
    }

    function readAllLocalVariables() external {
        Placeholder destination;
        uint msgValue;
        uint callGas;
        uint argument;
        destination.callMe{value: msgValue, gas: callGas}(argument);
    }
    
}

contract HighLevelCallWriteAll {
    uint retValue; 

    function writeAllStateVariables() external {
        Placeholder destination = new Placeholder();
        retValue =  destination.callMe(0);
    }

    function writeAllLocalVariables() external {
        Placeholder destination = new Placeholder();
        uint retValue;
        retValue =  destination.callMe(0);
    }
}

contract LowLevelCallReadAll {
    uint msgValue;
    uint callGas;
    address destination;
    uint argument;

    function readAllStateVariables() external {
        destination.call{value: msgValue, gas: callGas}(abi.encodeWithSignature("callMe(uint256)", argument));
    }

    function readAllLocalVariables() external {
        address destination;
        uint msgValue;
        uint callGas;
        uint argument;
        destination.call{value: msgValue, gas: callGas}(abi.encodeWithSignature("callMe(uint256)", argument));
    }
    
}

contract LowLevelCallWriteAll {
    bool success; 
    bytes data;

    function writeAllStateVariables() external {
        Placeholder destination = new Placeholder();
        (success, data) = address(destination).call(abi.encodeWithSignature("callMe(uint256)", 0));
    }

    function writeAllLocalVariables() external {
        Placeholder destination = new Placeholder();
        (bool success, bytes memory data) = address(destination).call(abi.encodeWithSignature("callMe(uint256)", 0));
    }
}

contract ReturnReadAll {
    uint stateVar;

    function readAllStateVariables() external returns (uint) {
        return stateVar;
    }

    function readAllLocalVariables() external returns (uint) {
        uint localVar;
        return localVar;
    }
}

contract NewStructureReadAll {
    uint a;
    uint b;

    struct S {
        uint x;
        uint y;
    }


    function readAllStateVariables() external {
        S({x: a, y: b});
    }

    function readAllLocalVariables() external {
        uint c;
        uint d;
        S({x: c, y: d});
    }
}

contract TypeConversionReadAll {
    uint stateVar;

    function readAllStateVariables() external {
        uint localVar = uint8(stateVar);
    }

    function readAllLocalVariables() external {
        uint8 localVar;
        uint(localVar);
    }
}

contract TypeConversionWriteAll {
    uint stateVar;

    function writeAllStateVariables() external {
        uint localVar;
        stateVar = uint8(localVar);
    }

    function writeAllLocalVariables() external {
        uint8 localVar = uint8(stateVar);
    }
}

contract IndexReadAll {
    uint[] stateVar;
    uint index;

    function readAllStateVariables() external {
        stateVar[index];
    }

    function readAllLocalVariables() external {
        uint[] memory localVar;
        uint index;
        stateVar[index] = localVar[index];
    }
}

contract IndexWriteAll {
    uint[] stateVar;

    function writeAllStateVariables() external {
        stateVar[0] = stateVar[0];
    }

    function writeAllLocalVariables() external {
        uint[] memory localVar;
        localVar[0] = stateVar[0];
    }
}

contract MemberReadAll {
    Placeholder stateVar;

    function readAllStateVariables() external {
        stateVar.callMe(0);
    }

    function readAllLocalVariables() external {
        Placeholder localVar;
        localVar.callMe(0);
    }
}

contract MemberWriteAll {
    struct S {
        uint x;
        uint y;
    }

    S stateVar;

    function writeAllStateVariables() external {
        stateVar.x = 0;
    }

    function writeAllLocalVariables() external {
        S memory localVar;
        localVar.x = 0;
    }
}

contract TransferReadAll {
    uint amt;
    address payable destination;

    function readAllStateVariables() external {
        destination.transfer(amt);
    }

    function readAllLocalVariables() external {
        uint localVar;
        address payable destination;
        destination.transfer(localVar);
    }
}

contract SendReadAll {
    uint amt;
    address payable destination;

    function readAllStateVariables() external {
        destination.send(amt);
    }

    function readAllLocalVariables() external {
        uint localVar;
        address payable destination;
        destination.send(localVar);
    }
}

contract UnaryReadAll{
    uint stateVar;

    function readAllStateVariables() external {
        stateVar++;
    }

    function readAllLocalVariables() external {
        uint localVar;
        localVar++;
    }
}

contract UnaryWriteAll {
    uint stateVar;

    function writeAllStateVariables() external {
        stateVar++;
    }

    function writeAllLocalVariables() external {
        uint localVar;
        localVar++;
    }
}

contract UnpackReadAll {
    uint stateVar1;
    uint stateVar2;

    function readAllStateVariables() external {
        (uint localVar1, uint localVar2) = (stateVar1, stateVar2);
    }

    function readAllLocalVariables() external {
        uint localVar1;
        uint localVar2;
        (stateVar1, stateVar2) = (localVar1, localVar2);
    }
}

contract UnpackWriteAll {
    uint stateVar1;
    uint stateVar2;

    function writeAllStateVariables() external {
        uint localVar1;
        uint localVar2;
        (stateVar1, stateVar2) = (localVar1, localVar2);
    }

    function writeAllLocalVariables() external {
        (uint localVar1, uint localVar2) = (stateVar1, stateVar2);
    }
}

contract LengthReadAll {
    uint[] lengthStateVar;

    function readAllStateVariables() external {
        lengthStateVar.length;
    }

    function readAllLocalVariables() external {
        uint[] memory lengthLocalVar;
        lengthLocalVar.length;
    }
}

contract LengthWriteAll {
    uint[] lengthStateVar;

    function writeAllStateVariables() external {
        lengthStateVar.push(1);
    }

    function writeAllLocalVariables() external {
        uint[] memory lengthLocalVar = new uint[](1);
        lengthLocalVar[0] = 1;
    }
}

contract InitArrayReadAll {
    uint[3] stateVar;

    function readAllStateVariables() external {
        uint[3] memory localVar = stateVar;
    }

    function readAllLocalVariables() external {
        uint localVar1;
        uint localVar2;
        uint localVar3;
        stateVar =  [localVar1, localVar2, localVar3];
    }
}

contract InitArrayWriteAll {
    uint[3] stateVar;

    function writeAllStateVariables() external {
        uint localVar1;
        uint localVar2;
        uint localVar3;
        stateVar =  [localVar1, localVar2, localVar3];
    }
    
    function writeAllLocalVariables() external {
        uint[3] memory localVar = stateVar;
    }

}

