
struct Z {
    int x;
    int y;
}
contract OtherTest {
    struct Z {
        int x;
        int y;
    }

    function myfunc() external {
        // https://github.com/crytic/slither/issues/1809
        Z memory z1 = Z(2,3);
        // https://github.com/crytic/slither/issues/2122
        DeleteTest.Z z2 = DeleteTest.Z.wrap(1); 

    }
}

contract DeleteTest {
   type Z is int;
}
