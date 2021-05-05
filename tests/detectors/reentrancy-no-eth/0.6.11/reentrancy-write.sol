// pragma solidity 0.4.26;

contract ReentrancyWrite {
    bool notCalled = true;

    function bad0() public {
        require(notCalled);
        (bool success,) = msg.sender.call("");
        if (!success) {
            revert();
        }
        notCalled = false;
    }

    function bad1(address target) public {
        require(notCalled);
        (bool success,) = msg.sender.call("");
        require(success);
        bad0();
    }

    function good() public {
        require(notCalled);
        notCalled = true;
        (bool success,) = msg.sender.call("");
        if (!success) {
            revert();
        }
    }

}
