interface Test:
    def foo() -> (int128, uint256): nonpayable

tester: Test

@internal
def foo() -> (int128, int128):
    return 2, 3

@external
def bar():
    a: int128 = 0
    b: int128 = 0
    (a, b) = self.foo()

    x: address = 0x0000000000000000000000000000000000000000
    c: uint256 = 0
    a, c = Test(x).foo()

@external
def baz():
    a: int128 = 0
    b: int128 = 0
    (a, b) = self.foo()

    x: address = 0x0000000000000000000000000000000000000000
    c: uint256 = 0
    a, c = self.tester.foo()

