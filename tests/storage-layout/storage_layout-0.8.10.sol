contract StorageLayout {
    uint248 packedUint = 1;
    bool packedBool = true;

    struct PackedStruct {
        bool b;
        uint248 a;
    }
    PackedStruct _packedStruct = PackedStruct(packedBool, packedUint);

    mapping (uint => PackedStruct) mappingPackedStruct;
    mapping (address => mapping (uint => PackedStruct)) deepMappingPackedStruct;

    mapping (address => mapping (uint => bool)) deepMappingElementaryTypes;

    address _address;
    string _string = "slither-read-storage";
    uint8 packedUint8 = 8;
    bytes8 packedBytes = "aaaaaaaa";

    enum Enum {
        a,
        b,
        c
    }
    Enum _enumA = Enum.a;
    Enum _enumB = Enum.b;
    Enum _enumC = Enum.c;

    uint256[3] fixedArray;
    uint256[3][] dynamicArrayOfFixedArrays;
    uint[][3] fixedArrayofDynamicArrays;
    uint[][] multidimensionalArray;

    constructor() {
        _address = address(this);
    }
    function store() external {
        mappingPackedStruct[packedUint] = _packedStruct; 

        deepMappingPackedStruct[_address][packedUint] = _packedStruct;

        deepMappingElementaryTypes[_address][1] = true;
        deepMappingElementaryTypes[_address][2] = true;

        fixedArray = [1, 2, 3];

        dynamicArrayOfFixedArrays.push(fixedArray);
        dynamicArrayOfFixedArrays.push([4, 5, 6]);

        fixedArrayofDynamicArrays[0].push(7);
        fixedArrayofDynamicArrays[1].push(8);
        fixedArrayofDynamicArrays[1].push(9);
        fixedArrayofDynamicArrays[2].push(10);
        fixedArrayofDynamicArrays[2].push(11);
        fixedArrayofDynamicArrays[2].push(12);

        multidimensionalArray.push([13]);
        multidimensionalArray.push([14, 15]);
        multidimensionalArray.push([16, 17, 18]);

    }
}