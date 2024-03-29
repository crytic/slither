from pathlib import Path
from slither import Slither

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_overrides(solc_binary_path) -> None:
    # pylint: disable=too-many-statements,too-many-locals
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(Path(TEST_DATA_DIR, "virtual_overrides.sol").as_posix(), solc=solc_path)

    test = slither.get_contract_from_name("Test")[0]
    test_virtual_func = test.get_function_from_full_name("myVirtualFunction()")
    assert test_virtual_func.is_virtual
    assert not test_virtual_func.is_override
    x = test.get_functions_overridden_by(test_virtual_func)
    assert len(x) == 0
    x = test_virtual_func.overridden_by
    assert len(x) == 5
    assert set(i.canonical_name for i in x) == set(
        ["A.myVirtualFunction()", "C.myVirtualFunction()", "X.myVirtualFunction()"]
    )

    a = slither.get_contract_from_name("A")[0]
    a_virtual_func = a.get_function_from_full_name("myVirtualFunction()")
    assert a_virtual_func.is_virtual
    assert a_virtual_func.is_override
    x = a.get_functions_overridden_by(a_virtual_func)
    assert len(x) == 2
    assert set(i.canonical_name for i in x) == set(["Test.myVirtualFunction()"])

    b = slither.get_contract_from_name("B")[0]
    b_virtual_func = b.get_function_from_full_name("myVirtualFunction()")
    assert not b_virtual_func.is_virtual
    assert b_virtual_func.is_override
    x = b.get_functions_overridden_by(b_virtual_func)
    assert len(x) == 2
    assert set(i.canonical_name for i in x) == set(["A.myVirtualFunction()"])
    assert len(b_virtual_func.overridden_by) == 0

    c = slither.get_contract_from_name("C")[0]
    c_virtual_func = c.get_function_from_full_name("myVirtualFunction()")
    assert not c_virtual_func.is_virtual
    assert c_virtual_func.is_override
    x = c.get_functions_overridden_by(c_virtual_func)
    assert len(x) == 2
    # C should not override B as they are distinct leaves in the inheritance tree
    assert set(i.canonical_name for i in x) == set(["Test.myVirtualFunction()"])

    y = slither.get_contract_from_name("Y")[0]
    y_virtual_func = y.get_function_from_full_name("myVirtualFunction()")
    assert y_virtual_func.is_virtual
    assert not y_virtual_func.is_override
    x = y_virtual_func.overridden_by
    assert len(x) == 1
    assert x[0].canonical_name == "Z.myVirtualFunction()"

    z = slither.get_contract_from_name("Z")[0]
    z_virtual_func = z.get_function_from_full_name("myVirtualFunction()")
    assert z_virtual_func.is_virtual
    assert z_virtual_func.is_override
    x = z.get_functions_overridden_by(z_virtual_func)
    assert len(x) == 4
    assert set(i.canonical_name for i in x) == set(
        ["Y.myVirtualFunction()", "X.myVirtualFunction()"]
    )

    k = slither.get_contract_from_name("K")[0]
    k_virtual_func = k.get_function_from_full_name("a()")
    assert not k_virtual_func.is_virtual
    assert k_virtual_func.is_override
    assert len(k_virtual_func.overrides) == 3
    x = k_virtual_func.overrides
    assert set(i.canonical_name for i in x) == set(["I.a()"])

    i = slither.get_contract_from_name("I")[0]
    i_virtual_func = i.get_function_from_full_name("a()")
    assert i_virtual_func.is_virtual
    assert not i_virtual_func.is_override
    assert len(i_virtual_func.overrides) == 0
    x = i_virtual_func.overridden_by
    assert len(x) == 1
    assert x[0].canonical_name == "K.a()"


def test_virtual_override_references_and_implementations(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.15")
    file = Path(TEST_DATA_DIR, "virtual_overrides.sol").as_posix()
    slither = Slither(file, solc=solc_path)
    funcs = slither.offset_to_objects(file, 29)
    assert len(funcs) == 1
    func = funcs.pop()
    assert func.canonical_name == "Test.myVirtualFunction()"
    assert {(x.start, x.end) for x in slither.offset_to_implementations(file, 29)} == {
        (20, 73),
        (102, 164),
        (274, 328),
        (357, 419),
    }

    funcs = slither.offset_to_objects(file, 111)
    assert len(funcs) == 1
    func = funcs.pop()
    assert func.canonical_name == "A.myVirtualFunction()"
    # A.myVirtualFunction() is implemented in A and also overridden in B
    assert {(x.start, x.end) for x in slither.offset_to_implementations(file, 111)} == {
        (102, 164),
        (190, 244),
    }

    # X is inherited by Z and Z.myVirtualFunction() overrides X.myVirtualFunction()
    assert {(x.start, x.end) for x in slither.offset_to_references(file, 341)} == {
        (514, 515),
        (570, 571),
    }
    # The reference to X in inheritance specifier is the definition of Z
    assert {(x.start, x.end) for x in slither.offset_to_definitions(file, 514)} == {(341, 343)}
    # The reference to X in the function override specifier is the definition of Z
    assert {(x.start, x.end) for x in slither.offset_to_definitions(file, 570)} == {(341, 343)}

    # Y is inherited by Z and Z.myVirtualFunction() overrides Y.myVirtualFunction()
    assert {(x.start, x.end) for x in slither.offset_to_references(file, 432)} == {
        (511, 512),
        (567, 568),
    }
    # The reference to Y in inheritance specifier is the definition of Z
    assert {(x.start, x.end) for x in slither.offset_to_definitions(file, 511)} == {(432, 434)}
    # The reference to Y in the function override specifier is the definition of Z
    assert {(x.start, x.end) for x in slither.offset_to_definitions(file, 567)} == {(432, 434)}

    # Name is abstract and has no implementation. It is inherited and implemented by Name2
    assert {(x.start, x.end) for x in slither.offset_to_implementations(file, 612)} == {(657, 718)}


def test_virtual_is_implemented(solc_binary_path):
    solc_path = solc_binary_path("0.8.15")
    file = Path(TEST_DATA_DIR, "virtual_overrides.sol").as_posix()
    slither = Slither(file, solc=solc_path)

    test2 = slither.get_contract_from_name("Test2")[0]
    f = test2.get_function_from_full_name("f()")
    assert f.is_virtual
    assert not f.is_implemented

    a2 = slither.get_contract_from_name("A2")[0]
    f = a2.get_function_from_full_name("f()")
    assert f.is_virtual
    assert f.is_implemented

    # Test.2f() is not implemented, but A2 inherits from Test2 and overrides f()
    assert {(x.start, x.end) for x in slither.offset_to_implementations(file, 759)} == {(809, 853)}
