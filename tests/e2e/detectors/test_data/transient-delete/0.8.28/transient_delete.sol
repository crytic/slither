pragma solidity 0.8.28;

// Flagged: transient delete + persistent delete on mapping element
contract TransientDeleteWithMapping {
    address transient _lock;
    mapping(uint256 => address) public delegates;

    function guarded() external {
        require(_lock == address(0), "locked");
        _lock = msg.sender;
        delete _lock;
    }

    function clearDelegate(uint256 id) external {
        delete delegates[id];
    }
}

// Flagged: transient delete + pop on persistent array
contract TransientDeleteWithPop {
    uint256 transient _temp;
    uint256[] public values;

    function run() external {
        _temp = 42;
        delete _temp;
    }

    function removeLast() external {
        values.pop();
    }
}

// Flagged: transient delete + delete on persistent struct
contract TransientDeleteWithStruct {
    struct Info {
        address owner;
        uint256 amount;
    }

    address transient _caller;
    Info public info;

    function run() external {
        _caller = msg.sender;
        delete _caller;
    }

    function clearInfo() external {
        delete info;
    }
}

// Flagged: transient delete + delete on persistent array
contract TransientDeleteWithArray {
    bool transient _flag;
    bool[] public flags;

    function run() external {
        _flag = true;
        delete _flag;
    }

    function clearFlags() external {
        delete flags;
    }
}

// Not flagged: transient delete but no persistent clearing
contract TransientDeleteNoPersistent {
    address transient _lock;

    function guarded() external {
        require(_lock == address(0), "locked");
        _lock = msg.sender;
        delete _lock;
    }
}

// Not flagged: zero assignment instead of delete on transient
contract TransientZeroAssign {
    address transient _lock;
    mapping(uint256 => address) public delegates;

    function guarded() external {
        require(_lock == address(0), "locked");
        _lock = msg.sender;
        _lock = address(0);
    }

    function clearDelegate(uint256 id) external {
        delete delegates[id];
    }
}
