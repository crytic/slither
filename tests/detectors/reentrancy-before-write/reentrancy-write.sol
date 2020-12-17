pragma solidity 0.4.26;

contract ReentrancyWrite {
    bool notCalled = true;

    function bad0() public {
        require(notCalled);
        if (!(msg.sender.call())) {
            revert();
        }
        notCalled = false;
    }

    function bad1(address target) public {
        require(notCalled);
        (bool success) = msg.sender.call();
        require(success);
        bad0();
    }

    function good() public {
        require(notCalled);
        notCalled = true;
        if (!(msg.sender.call())) {
            revert();
        }
    }

}
