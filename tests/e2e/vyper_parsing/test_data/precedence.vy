@internal
def fa() -> uint256:
    return 1

@internal
def fb() -> uint256:
    raise

@external
def foo(x: uint256) -> bool:
    return x not in [self.fa(), self.fb()]


