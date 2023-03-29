pragma abicoder v2;
type MyAddress is address;

contract C {
    MyAddress[] public addresses;
    function f(MyAddress[] calldata _addresses) external {
        for (uint i = 0; i < _addresses.length; i++) {
            MyAddress.unwrap(_addresses[i]).call("");
        }
        addresses = _addresses;
    }
    function g(MyAddress[] memory _addresses) external {
        for (uint i = 0; i < _addresses.length; i++) {
            MyAddress.unwrap(_addresses[i]).call("");
        }
        addresses = _addresses;
    }
    function test_f() external returns (bool) {
        clean();
        MyAddress[] memory test = new MyAddress[](3);
        test[0] = MyAddress.wrap(address(21));
        test[1] = MyAddress.wrap(address(22));
        test[2] = MyAddress.wrap(address(23));
        // this.f(test);
        test_equality(test);
        return true;
    }
    function test_g() external returns (bool) {
        clean();
        MyAddress[] memory test = new MyAddress[](5);
        test[0] = MyAddress.wrap(address(24));
        test[1] = MyAddress.wrap(address(25));
        test[2] = MyAddress.wrap(address(26));
        test[3] = MyAddress.wrap(address(27));
        test[4] = MyAddress.wrap(address(28));
        this.g(test);
        test_equality(test);
        return true;
    }
    function clean() internal {
        delete addresses;
    }
    function test_equality(MyAddress[] memory _addresses) internal view {
        require (_addresses.length == addresses.length);
        for (uint i = 0; i < _addresses.length; i++) {
            require(MyAddress.unwrap(_addresses[i]) == MyAddress.unwrap(addresses[i]));
        }
    }
}
