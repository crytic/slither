@external
@view
def compute(p: uint256):
    a: uint256 = p
    b: uint256 = 1
    c: uint256 = 0

    if b > 0:
        old_a: uint256 = 1
        old_c: uint256 = 2
        if p > old_a:
            c = unsafe_div(old_a * 10**18, p)
            if c < 10**36 / 1:
                a = unsafe_div(old_a * 1, 10**18)
                c = 10**36 / 1
        else:
            c = unsafe_div(p * 10**18, old_a)
            if c < 10**36 / 1:
                a = unsafe_div(old_a * 10**18, 1)
                c = 10**36 / 1

        c = 1
