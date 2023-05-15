contract A {
    function foo() public {
        assembly {
            function f() { function z() { function x() { g() } x() } z() }
            function w() { function a() {} function b() { a() } b() }
            function g() {
                f()
            }
            g()
        }
    }
}
