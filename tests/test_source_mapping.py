from slither import Slither
from slither.core.declarations import Function


def test_source_mapping():
    slither = Slither("tests/src_mapping/inheritance.sol")

    # Check if A.f() is at the offset 27
    functions = slither.offset_to_objects("tests/src_mapping/inheritance.sol", 27)
    print(functions)
    assert len(functions) == 1
    function = functions.pop()
    assert isinstance(function, Function)
    assert function.canonical_name == "A.f()"

    # Only one definition for A.f()
    assert {
        (x.start, x.end)
        for x in slither.offset_to_definitions("tests/src_mapping/inheritance.sol", 27)
    } == {(26, 28)}
    # Only one reference for A.f(), in A.test()
    assert {
        (x.start, x.end)
        for x in slither.offset_to_references("tests/src_mapping/inheritance.sol", 27)
    } == {(92, 93)}
    # Only one implementation for A.f(), in A.test()
    assert {
        (x.start, x.end)
        for x in slither.offset_to_implementations("tests/src_mapping/inheritance.sol", 27)
    } == {(17, 53)}

    # Check if C.f() is at the offset 203
    functions = slither.offset_to_objects("tests/src_mapping/inheritance.sol", 203)
    assert len(functions) == 1
    function = functions.pop()
    assert isinstance(function, Function)
    assert function.canonical_name == "C.f()"

    # Only one definition for C.f()
    assert {
        (x.start, x.end)
        for x in slither.offset_to_definitions("tests/src_mapping/inheritance.sol", 203)
    } == {(202, 204)}
    # Two references for C.f(), in A.test() and C.test2()
    assert {
        (x.start, x.end)
        for x in slither.offset_to_references("tests/src_mapping/inheritance.sol", 203)
    } == {(270, 271), (92, 93)}
    # Only one implementation for A.f(), in A.test()
    assert {
        (x.start, x.end)
        for x in slither.offset_to_implementations("tests/src_mapping/inheritance.sol", 203)
    } == {(193, 230)}

    # Offset 93 is the call to f() in A.test()
    # This can lead to three differents functions, depending on the current contract's context
    functions = slither.offset_to_objects("tests/src_mapping/inheritance.sol", 93)
    print(functions)
    assert len(functions) == 3
    for function in functions:
        assert isinstance(function, Function)
        assert function.canonical_name in ["A.f()", "B.f()", "C.f()"]

    # There are three definitions possible (in A, B or C)
    assert {
        (x.start, x.end)
        for x in slither.offset_to_definitions("tests/src_mapping/inheritance.sol", 93)
    } == {(26, 28), (202, 204), (138, 140)}

    # There are two references possible (in A.test() or C.test2() )
    assert {
        (x.start, x.end)
        for x in slither.offset_to_references("tests/src_mapping/inheritance.sol", 93)
    } == {(92, 93), (270, 271)}

    # There are three implementations possible (in A, B or C)
    assert {
        (x.start, x.end)
        for x in slither.offset_to_implementations("tests/src_mapping/inheritance.sol", 93)
    } == {(17, 53), (193, 230), (129, 166)}


test_source_mapping()
