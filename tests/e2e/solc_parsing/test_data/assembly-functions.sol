contract A {
    function foo() public {
        assembly {
            function f() { function z() { function x() { g() } x() } z() }
            function g() {
                f()
            }
            g()
        }
    }
}
