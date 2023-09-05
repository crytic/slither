@external
def f(): 
    for i in range(100):
        if (i > 100):
            break

        if (i < 3):
            continue
        x: uint256 = 10
        for j in range(10):
            if (j > 10):
                continue

            if (j < 3):
                break

            x -= 1
