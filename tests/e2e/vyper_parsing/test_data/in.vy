enum Roles:
    A
    B

roles: public(HashMap[address, Roles])

@external
def baz(x: Roles) -> bool:
    if x in (Roles.A | Roles.B):
        return True
    if x not in (Roles.A | Roles.B):
        return False

    return False

@external
def bar(x: Roles) -> bool:

    if x in self.roles[self]:
        return True
    if x not in self.roles[self]:
        return False

    return False

@external
def foo(x: int128) -> bool:
    a: int128 = 0
    b: int128 = 0

    if x in [a, b]:
        return True
    if x not in [a, b]:
        raise "nope"

    return False