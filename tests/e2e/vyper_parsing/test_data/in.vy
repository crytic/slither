enum Roles:
    A
    B

roles: public(HashMap[address, Roles])

@external
def bar(x: Roles) -> bool:
    a: int128 = 0
    b: int128 = 0

    if x in self.roles[self]:
        return True
    return False

@external
def foo(x: int128) -> bool:
    a: int128 = 0
    b: int128 = 0

    if x in [a, b]:
        return True
    return False