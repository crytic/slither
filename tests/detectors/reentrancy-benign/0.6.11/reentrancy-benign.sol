// pragma solidity ^0.4.0;

contract ReentrancyBenign {
    uint8 anotherVariableToChange;
    uint8 counter = 0;

    function bad0() public {
        (bool success,) = msg.sender.call("");
        if (!success) {
            revert();
        }
        counter += 1;
    }

    function bad1(address target) public {
        (bool success,) = target.call("");
        require(success);
        counter += 1;
    }

    function bad2(address target) public {
        (bool success,) = target.call("");
        if (success) {
            address(target).call.value(1000)("");
            counter += 1;
        }
        else {
            revert();
        }
    }

    function bad3(address target) public {
        externalCaller(target);
        varChanger();
        ethSender(target);
    }

    function bad4(address target) public {
        externalCaller(target);
        ethSender(address(0));
        varChanger();
        address(target).call.value(2)("");
    }

    function bad5(address target) public {
        ethSender(address(0));
        varChanger();
        ethSender(address(0));
    }

    function externalCaller(address target) private {
        address(target).call("");
    }

    function ethSender(address target) private {
        address(target).call.value(1)("");
    }

    function varChanger() private {
        anotherVariableToChange++;
    }
}