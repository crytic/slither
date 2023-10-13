counter: uint256
config: bool
@internal
def b(y: uint256, config: bool = True):
    if config:
        self.counter = y

@external
def a(x: uint256, z: bool):
    self.b(x)
    self.b(1, self.config)
    self.b(1, z)