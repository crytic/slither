pragma solidity >=0.4.16 <0.7.0;
contract Contract {
    function f() public returns (int) {
        bool cond = true;
        int a = 5;
        for (int c = a; c < 10; c++) {
           if (a == 0) { break; }
            else { a--; }
        }
        return a;
    }
}