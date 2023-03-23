struct abc {       
    uint8 small1;
    uint8 small2;
    bytes32 bigboy;
    uint8 small3;
    mapping(address => mapping(uint => bool)) someNestedMapping;
    uint8 small4;
}

struct easy_fix {
    uint8 small1;
    uint256 big;
    uint8 small2;
}

struct easy_already_optimized {
    uint8 small1;
    uint8 small2;
    uint256 big;
}

struct easy_cant_optimize {
    uint8 small1;
    uint8 small2;
    uint8 small3;
}

struct cant_pack_arrays {
    bytes16[1] arr1;
    uint256 x;       
    bytes16[1] arr2;
}

struct cant_pack_arrays_can_pack_others {
    bytes16[1] arr1;
    uint128 half1;
    uint256 big1;       
    uint128 half2;
    bytes16[1] arr2;
}

struct hard_struct1 {
    uint248 s31bytes1;
    uint248 s31bytes2;
    uint248 s31bytes3;
    uint8 s1byte1;
    uint8 s1byte2;
    uint8 s1byte3;
}

struct hard_struct2 {
    uint232 s29bytes;
    uint240 s30bytes;
    uint248 s31bytes;
    uint24 s3bytes;
    uint16 s2bytes;
    uint8 s1byte;
}


library MyMath {
    struct mymathlibstruct {
        bytes1 math1;
        bytes32 math2big;
        bytes1 math3;
        abc nestedStruct;
        bytes1 math4;
    }
    function add(uint x, uint y) internal pure returns (uint) {
        uint z = x + y;
        return z;
    }
}

contract Hello {
    bytes1 sml1;
    MyMath.mymathlibstruct doubleNested;
    bytes1 sml2;
    bytes32 bigpapi1;
    bytes1 sml3;
    mapping(uint24 => uint64) someMapping;
    bytes1 
        
        sm14;
}

contract HelloWorld is Hello {
    bool aa;
    uint256 xx;
    bool bb;
    abc innerStruct;
    bool cc;

    struct random_struct_medium {
        bytes9 var1;
        int32 var2;
        bytes12 var3;
        uint256 var4;
        int8 var5;
        bytes16 var6;
        MyMath.mymathlibstruct innerStruct1;
        bytes15 var7;
        uint32 var8;
        bytes12 var9;
        int144 var10;
        uint208 var11;
        int136 var12;
        abc innerStruct2;
        int256 var13;
        int176 var14;
        uint56 var15;
    }

    struct random_struct_large {
        uint152 var1;
        uint168 var2;
        uint8 var3;
        bytes17 var4;
        int16 var5;
        int152 var6;
        int256 var7;
        uint200 var8;
        bytes21 var9;
        uint224 var10;
        int240 var11;
        int120 var12;
        uint232 var13;
        uint88 var14;
        uint176 var15;
        bytes20 var16;
        int200 var17;
        uint232 var18;
        bytes5 var19;
        int224 var20;
        uint112 var21;
        int168 var22;
        int56 var23;
        uint200 var24;
        uint56 var25;
        bytes3 var26;
        int24 var27;
        int208 var28;
        uint40 var29;
        uint24 var30;
        int16 var31;
        bytes var32;
        int32 var33;
        int184 var34;
        uint16 var35;
        uint128 var36;
        int104 var37;
        uint152 var38;
        int208 var39;
        int168 var40;
        bytes17 var41;
        bytes27 var42;
        uint32 var43;
        int112 var44;
        uint128 var45;
        bytes21 var46;
        int72 var47;
        uint240 var48;
        bytes21 var49;
        uint160 var50;
        int208 var51;
        bytes12 var52;
        bytes27 var53;
        int72 var54;
        int24 var55;
        bool var56;
        bytes15 var57;
        uint184 var58;
        uint208 var59;
        bytes19 var60;
        int120 var61;
        uint144 var62;
        int128 var63;
        address var64;
        int32 var65;
        int72 var66;
        int80 var67;
        int224 var68;
        int200 var69;
        uint16 var70;
        int120 var71;
        bytes10 var72;
        int104 var73;
        int24 var74;
        int216 var75;
        uint176 var76;
        uint56 var77;
        bytes4 var78;
        bytes22 var79;
        bytes29 var80;
        int216 var81;
        bytes16 var82;
        int240 var83;
        bytes16 var84;
        bytes3 var85;
        uint120 var86;
        uint136 var87;
        uint88 var88;
        uint128 var89;
        bytes1 var90;
        uint120 var91;
        bytes5 var92;
        uint40 var93;
        int128 var94;
        string var95;
        int232 var96;
        bytes23 var97;
        int64 var98;
        bytes26 var99;
        uint136 var100;
    }

    function isThree(
        int a
    ) external pure returns (bool) {
        return a == 3;
    }

}

/* code to generate the random structs

import random

uint_types = ["uint8", "uint16", "uint24", "uint32", "uint40", "uint48", "uint56", "uint64", "uint72", "uint80", "uint88", "uint96", "uint104", "uint112", "uint120", "uint128", "uint136", "uint144", "uint152", "uint160", "uint168", "uint176", "uint184", "uint192", "uint200", "uint208", "uint216", "uint224", "uint232", "uint240", "uint256", "uint248" ]
int_types = ["int", "int8", "int16", "int24", "int32", "int40", "int48", "int56", "int64", "int72", "int80", "int88", "int96", "int104", "int112", "int120", "int128", "int136", "int144", "int152", "int160", "int168", "int176", "int184", "int192", "int200", "int208", "int216", "int224", "int232", "int240", "int248", "int256"]
byte_types = ["bytes1", "bytes2", "bytes3", "bytes4", "bytes5", "bytes6", "bytes7", "bytes8", "bytes9", "bytes10", "bytes11", "bytes12", "bytes13", "bytes14", "bytes15", "bytes16", "bytes17", "bytes18", "bytes19", "bytes20", "bytes21", "bytes22", "bytes23", "bytes24", "bytes25", "bytes26", "bytes27", "bytes28", "bytes29", "bytes30", "bytes31", "bytes32", ]
other = ["address", "address payable", "bool", "string", "bytes"]

all_types = uint_types + int_types + byte_types + other

def get_random_type():
    return random.choice(all_types)

def get_struct_str(element_count):
    s = "struct AAA {\n"
    for i in range(1, 1+element_count):
        s += f"\t{get_random_type()} var{i};\n"
    s += "}"
    return s
    
print(get_struct_str(100))
*/

/*
This file is for testing. The way I use this file:

in ipython3:

from slither import Slither
slither = Slither('coolbeans.sol')
slither = Slither('/home/guy/testsol/coolbeans.sol')

*/