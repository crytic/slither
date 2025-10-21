contract ArrayLengthAssignment {
    uint x;
    uint120[] arr;
    uint120[] arr2;
    uint256[] arr3;
    constructor() public {
        x = 7;
    }

    struct TestStructWithArray {
        uint[] x;
        uint[][] y;
    }
    struct TestStructWithStructWithArray {
        TestStructWithArray subStruct;
        uint[] z;
    }

    TestStructWithArray a;
    TestStructWithStructWithArray b;

    function f(uint param, uint param2) public {
        x += 1;
        if(x > 3) {
            arr.length = 7;
            arr.length = param;
        }
        else{
            // Array length that is incremented/decremented should not be found.
            x = arr2.length++;
            x = 7 + 3;
        }

        // Array length setting in structs should not be detected too.
        a.x.length++;
        a.x.length = param;
    

        // Array length setting in embedded structs should not be detected too.
        b.subStruct.x.length--;
        b.subStruct.x.length = param + 1;

        arr3[0] = param2;
        arr3.length++;
    }
}
