// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Diamond inheritance pattern to test super call resolution in inherited functions
// C3 linearization for D: D -> C -> B -> A
//
// Expected super call targets:
// - D.setValue super -> C.setValue
// - C.setValue (in D's context) super -> B.setValue  (NOT A!)
// - B.setValue (in D's context) super -> A.setValue

contract DiamondA {
    uint256 public valueA;

    function setValue(uint256 _value) public virtual {
        valueA = _value;
    }
}

contract DiamondB is DiamondA {
    uint256 public valueB;

    function setValue(uint256 _value) public virtual override {
        super.setValue(_value);
        valueB = _value * 2;
    }
}

contract DiamondC is DiamondA {
    uint256 public valueC;

    function setValue(uint256 _value) public virtual override {
        super.setValue(_value);
        valueC = _value * 3;
    }
}

contract DiamondD is DiamondB, DiamondC {
    uint256 public valueD;

    function setValue(uint256 _value) public override(DiamondB, DiamondC) {
        super.setValue(_value);
        valueD = _value * 4;
    }
}
