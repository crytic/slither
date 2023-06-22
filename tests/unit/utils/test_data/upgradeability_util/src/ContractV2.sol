pragma solidity ^0.8.2;

import "./ProxyStorage.sol";
import "./ERC20.sol";

contract ContractV2 is ProxyStorage {
    uint private stateA = 0;
    uint private stateB = 0;
    uint constant CONST = 32;
    bool bug = false;
    uint private stateC = 0;

    function f(uint x) public {
        if (msg.sender == admin) {
            stateA = x;
        }
    }

    function g(uint y) public {
        if (checkA()) {
            stateB = y - 10;
        }
    }

    function h() public {
        if (checkB()) {
            bug = true;
        }
    }

    function i() public {
        stateC = stateC + 1;
    }

    function checkA() internal returns (bool) {
        return stateA % CONST == 1;
    }

    function checkB() internal returns (bool) {
        return stateB == 32;
    }

    function erc20Transfer(address erc20, address to, uint256 amount) public returns (bool) {
        return ERC20(erc20).transfer(to, amount);
    }
}
