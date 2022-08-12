contract C {
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

    struct easy_cant_optimized {
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

    // code used to generate the random structs is below

    struct small_random_party {
        bool short1;
        address addr1;
        bytes27 var6;
        uint200 var1;
        int24 var2;
        uint168 var4;
        bytes31 long1;
        int24 var5;
        string long2;
    }

    /* Code to generate random struct:

    import random

    uint_types = ["uint8", "uint16", "uint24", "uint32", "uint40", "uint48", "uint56", "uint64", "uint72", "uint80", "uint88", "uint96", "uint104", "uint112", "uint120", "uint128", "uint136", "uint144", "uint152", "uint160", "uint168", "uint176", "uint184", "uint192", "uint200", "uint208", "uint216", "uint224", "uint232", "uint240", "uint256", "uint248" ]
    int_types = ["int", "int8", "int16", "int24", "int32", "int40", "int48", "int56", "int64", "int72", "int80", "int88", "int96", "int104", "int112", "int120", "int128", "int136", "int144", "int152", "int160", "int168", "int176", "int184", "int192", "int200", "int208", "int216", "int224", "int232", "int240", "int248", "int256"]
    byte_types = ["bytes1", "bytes2", "bytes3", "bytes4", "bytes5", "bytes6", "bytes7", "bytes8", "bytes9", "bytes10", "bytes11", "bytes12", "bytes13", "bytes14", "bytes15", "bytes16", "bytes17", "bytes18", "bytes19", "bytes20", "bytes21", "bytes22", "bytes23", "bytes24", "bytes25", "bytes26", "bytes27", "bytes28", "bytes29", "bytes30", "bytes31", "bytes32", ]
    other = ["address", "bool", "string", "bytes"]

    all_types = uint_types + int_types + byte_types + other

    def get_random_type():
        return random.choice(all_types)

    def get_struct_str(element_count):
        s = "struct AAA {\n"
        for i in range(1, 1+element_count):
            s += f"\t{get_random_type()} var{i};\n"
        s += "}"
        return s
        
    print(get_struct_str(3))

    */
}