pragma solidity ^0.5.0;
contract Locked{

    function receive() payable public{
        require(msg.value > 0);
    }

}

contract Send{
    address payable owner = msg.sender;
    
    function withdraw() public{
        owner.transfer(address(this).balance);
    }
}

contract Unlocked is Locked, Send{

    function withdraw() public{
        super.withdraw();
    }

}

// Still reported because solidity < 0.6.0 doesn't have assembly in the AST
contract UnlockedAssembly is Locked{

    function withdraw() public {
        assembly {
            let success := call(gas(), caller(),100,0,0,0,0)    
        }
    }

}

contract OnlyLocked is Locked{ }
