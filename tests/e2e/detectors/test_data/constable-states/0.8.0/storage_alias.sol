// adapted from https://github.com/crytic/slither/issues/2659
// State variables written through a storage reference passed to a library or internal function

library StorageSlot {
    struct StringSlot {
        string value;
    }

    function getStringSlot(string storage store) internal pure returns (StringSlot storage r) {
        assembly {
            r.slot := store.slot
        }
    }
}

library ShortStrings {
    // OpenZeppelin ShortStrings.toShortStringWithFallback pattern
    function toShortStringWithFallback(string memory value, string storage store) internal returns (bytes32) {
        if (bytes(value).length < 32) {
            return bytes32(bytes(value).length);
        } else {
            StorageSlot.getStringSlot(store).value = value;
            return bytes32(type(uint256).max);
        }
    }
}

library L {
    struct S {
        string value;
    }

    event Log(string s);

    function setThroughSlot(string storage store, string memory v) internal {
        S storage s;
        assembly {
            s.slot := store.slot
        }
        s.value = v;
    }

    function append(bytes storage b) internal {
        b.push(0x01);
    }

    function length(string storage s) internal view returns (uint256) {
        return bytes(s).length;
    }

    function log(string storage s) internal {
        emit Log(s);
    }
}

contract StorageAlias {
    using ShortStrings for string;
    using L for bytes;

    bytes32 private immutable _name;

    // Written through a storage reference: should not be reported
    string private _nameFallback;
    string private _slotAlias;
    bytes private _appended;
    bytes private _appendedThroughPointer;
    string private _forwarded;

    // Only read through a storage reference: should be reported
    string private _readView;
    string private _readNonView;

    constructor(string memory name) {
        _name = name.toShortStringWithFallback(_nameFallback);
        L.setThroughSlot(_slotAlias, name);
    }

    function append() external {
        _appended.append();
    }

    function appendThroughPointer() external {
        bytes storage p = _appendedThroughPointer;
        L.append(p);
    }

    function forward(string memory v) external {
        _set(_forwarded, v);
    }

    function _set(string storage store, string memory v) internal {
        L.setThroughSlot(store, v);
    }

    function read() external returns (uint256) {
        L.log(_readNonView);
        return L.length(_readView);
    }
}
