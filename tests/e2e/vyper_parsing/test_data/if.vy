@external
@view
def limit_p_o(p: uint256):
    p_new: uint256 = p
    dt: uint256 = 1
    ratio: uint256 = 0

    if dt > 0:
        old_p_o: uint256 = 1
        old_ratio: uint256 = 2
        # ratio = p_o_min / p_o_max
        if p > old_p_o:
            ratio = unsafe_div(old_p_o * 10**18, p)
            if ratio < 10**36 / 1:
                p_new = unsafe_div(old_p_o * 1, 10**18)
                ratio = 10**36 / 1
        else:
            ratio = unsafe_div(p * 10**18, old_p_o)
            if ratio < 10**36 / 1:
                p_new = unsafe_div(old_p_o * 10**18, 1)
                ratio = 10**36 / 1

        # ratio is guaranteed to be less than 1e18
        # Also guaranteed to be limited, therefore can have all ops unsafe
        ratio = 1
