pragma solidity ^0.4.24;

contract Complex {
    int numberOfSides = 7;
    string shape;
    uint i0 = 0;
    uint i1 = 0;
    uint i2 = 0;
    uint i3 = 0;
    uint i4 = 0;
    uint i5 = 0;
    uint i6 = 0;
    uint i7 = 0;
    uint i8 = 0;
    uint i9 = 0;
    uint i10 = 0;


    function computeShape() external {
        if (numberOfSides <= 2) {
            shape = "Cant be a shape!";
        } else if (numberOfSides == 3) {
            shape = "Triangle";
        } else if (numberOfSides == 4) {
            shape = "Square";
        } else if (numberOfSides == 5) {
            shape = "Pentagon";
        } else if (numberOfSides == 6) {
            shape = "Hexagon";
        } else if (numberOfSides == 7) {
            shape = "Heptagon";
        } else if (numberOfSides == 8) {
            shape = "Octagon";
        } else if (numberOfSides == 9) {
            shape = "Nonagon";
        } else if (numberOfSides == 10) {
            shape = "Decagon";
        } else if (numberOfSides == 11) {
            shape = "Hendecagon";
        } else {
            shape = "Your shape is more than 11 sides.";
        }
    }

    function complexExternalWrites() external {
        Increment test1 = new Increment();
        test1.increaseBy1();
        test1.increaseBy1();
        test1.increaseBy1();
        test1.increaseBy1();
        test1.increaseBy1();
        
        Increment test2 = new Increment();
        test2.increaseBy1();

        address test3 = new Increment();
        test3.call(bytes4(keccak256("increaseBy2()")));

        address test4 = new Increment();
        test4.call(bytes4(keccak256("increaseBy2()")));
    }

    function complexStateVars() external {
        i0 = 1;
        i1 = 1;
        i2 = 1;
        i3 = 1;
        i4 = 1;
        i5 = 1;
        i6 = 1;
        i7 = 1;
        i8 = 1;
        i9 = 1;
        i10 = 1;
    }
}

contract Increment {
    uint i = 0;

    function increaseBy1() public {
        i += 1;
    }

    function increaseBy2() public {
        i += 2;
    }
}