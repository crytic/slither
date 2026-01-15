struct X:
   y: int8


@external
def test() -> X:
    return X({y: 1})
