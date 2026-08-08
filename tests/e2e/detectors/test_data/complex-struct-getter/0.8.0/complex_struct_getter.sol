// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// --- Should be flagged ---

contract DirectArrayMapping {
    struct Config {
        address owner;
        uint256[] limits;
        mapping(address => bool) whitelist;
    }
    Config public config;
}

contract NestedStruct {
    struct Inner {
        uint256[] values;
    }
    struct Outer {
        Inner data;
        string name;
    }
    Outer public settings;
}

contract MappingOnly {
    struct Permissions {
        uint256 level;
        mapping(address => bool) allowed;
    }
    Permissions public permissions;
}

// --- Should NOT be flagged ---

contract SimpleStruct {
    struct Info {
        address owner;
        uint256 balance;
        string name;
    }
    Info public info;
}

contract PrivateComplex {
    struct Data {
        uint256[] items;
        mapping(address => uint256) balances;
    }
    Data internal data;

    function getData() external view returns (uint256[] memory) {
        return data.items;
    }
}

contract NoStruct {
    uint256 public value;
    address public owner;
}

contract NestedSimple {
    struct InnerSimple {
        uint256 x;
        uint256 y;
    }
    struct OuterSimple {
        InnerSimple point;
        string label;
    }
    OuterSimple public shape;
}
