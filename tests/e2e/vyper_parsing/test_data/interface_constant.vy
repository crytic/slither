struct MyStruct:
    liquidation_range: address
MY_CONSTANT: constant(uint256) =  50
interface MyInterface:
    def my_func(a: int256, b: DynArray[uint256, MY_CONSTANT]) -> MyStruct: nonpayable


