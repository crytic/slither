
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
        Z memory z = Z(2,3);
    }
}

contract DeleteTest {
   type Z is int;
}
