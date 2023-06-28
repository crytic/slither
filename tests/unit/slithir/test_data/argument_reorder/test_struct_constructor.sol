contract StructConstructorTest {
    struct S {
        int x;
        int y;
    }

    function test() external {
        S memory p = S({x: 2, y: 3});
        S memory q = S({y: 4, x: 5});
    }
}
