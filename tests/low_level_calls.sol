pragma solidity ^0.4.24;


contract Sender {
    function send(address _receiver) payable {
        _receiver.call.value(msg.value).gas(7777)();
    }
}


contract Receiver {
    uint public balance = 0;

    function () payable {
        balance += msg.value;
    }
}