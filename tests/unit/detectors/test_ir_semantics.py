"""Real-solc checks of migration warnings and their negative controls."""

import os
from pathlib import Path

import pytest
from solc_select import solc_select

from slither import Slither
from slither.detectors.compiler_bugs.ir_semantics import (
    IRConstructorOrder,
    IRRepeatedModifier,
)


@pytest.fixture(scope="module", params=["0.8.13", "0.8.26"])
def compiler(request):
    version = request.param
    if not solc_select.artifact_path(version).exists():
        solc_select.install_artifacts([version])
    return str(solc_select.artifact_path(version))


def analyze(tmp_path: Path, compiler: str, source: str, detector):
    target = tmp_path / "Test.sol"
    target.write_text("// SPDX-License-Identifier: MIT\npragma solidity >=0.8.13;\n" + source)
    slither = Slither(str(target), solc=compiler, compile_force_framework="solc")
    slither.register_detector(detector)
    return [result for results in slither.run_detectors() for result in results]


@pytest.mark.parametrize(
    "initializer, expected",
    [
        ("x", 1),
        ("readX()", 1),
        ("outer()", 1),
        ("x + 3", 1),
        ("42", 0),
        ("z", 0),
    ],
)
def test_initializer_reads(tmp_path, compiler, initializer, expected):
    source = f"""
contract Base {{
 uint internal x;
 uint internal z = 9;
 constructor() {{ x = 42; }}
 function readX() internal view returns(uint) {{ return x; }}
 function outer() internal view returns(uint) {{ return readX(); }}
}}
contract Derived is Base {{ uint public y = {initializer}; }}
"""
    results = analyze(tmp_path, compiler, source, IRConstructorOrder)
    assert len(results) == expected
    if expected:
        assert "Base.constructor()" in results[0]["description"]
        assert "Derived.y" in results[0]["description"]


@pytest.mark.parametrize(
    "source, expected",
    [
        ("contract C {uint x; uint y=x; constructor(){x=42;}}", 0),
        ("contract A {uint x=42;} contract B is A {uint y=x;}", 0),
        ("contract A {uint x; constructor(){x=42;}} contract B is A {uint immutable y=x;}", 1),
        (
            "contract A {uint x; constructor(){x=42;}} contract B is A {uint y=x;} contract C is B {}",
            1,
        ),
        (
            "contract A {uint x; constructor(){x=42;}} contract B is A {uint y=x;} contract C is A {uint z=x;}",
            2,
        ),
        (
            "contract A {uint x; constructor(){set();} function set() internal {x=42;}} contract B is A {uint y=x;}",
            1,
        ),
        ("contract A {uint x;} contract B is A {uint y=x; constructor(){x=42;}}", 0),
    ],
)
def test_constructor_context(tmp_path, compiler, source, expected):
    assert len(analyze(tmp_path, compiler, source, IRConstructorOrder)) == expected


@pytest.mark.parametrize(
    "modifier, body, expected",
    [
        ("_; _;", "return ++a;", 1),
        ("_;", "return ++a;", 0),
        ("if(a>0) {_;} else {_;}", "return ++a;", 0),
        ("for(uint i=0;i<2;i++){_;}", "return ++a;", 1),
        ("if(a>0){_; _;}", "return ++a;", 1),
        ("_; _;", "return a;", 0),
        ("_; _;", "a=3; return ++a;", 0),
        ("_; _;", "if(a==0) {a=3;} return ++a;", 1),
        ("_; _;", "r+=1;", 1),
        ("_; _;", "r=1;", 0),
        ("_; _;", "if(a>0){r=1;}", 1),
        ("_; _;", "if(a>0){r=1;} else {r=2;}", 0),
        ("_; _;", "if(a>0){r=1;} else {revert();}", 0),
        ("_; _;", "r=1; r+=1;", 0),
        ("_; _;", "return 7;", 0),
        ("_; revert(); _;", "return ++a;", 0),
        ("if(a>0){_;} _;", "return ++a;", 1),
    ],
)
def test_repeated_path_and_value_lifetime(tmp_path, compiler, modifier, body, expected):
    source = f"""
contract C {{
 modifier m(uint a) {{{modifier}}}
 function f(uint a) public pure m(a) returns(uint r) {{{body}}}
}}
"""
    assert len(analyze(tmp_path, compiler, source, IRRepeatedModifier)) == expected


def test_memory_alias_not_stack_reset(tmp_path, compiler):
    source = """
contract C {
 modifier twice(){_; _;}
 function f(uint[] memory a) public pure twice returns(uint) {a[0]++; return a[0];}
}
"""
    assert not analyze(tmp_path, compiler, source, IRRepeatedModifier)


def test_inherited_modifier_and_function(tmp_path, compiler):
    source = """
contract A {
 modifier twice(){_; _;}
 function f(uint a) public pure twice returns(uint){return ++a;}
}
contract B is A {}
"""
    results = analyze(tmp_path, compiler, source, IRRepeatedModifier)
    assert len(results) == 1
    assert "A.f(uint256)" in results[0]["description"]


def test_two_derived_contexts(tmp_path, compiler):
    source = """
contract A {
 modifier twice(){_; _;}
 function f(uint a) public pure twice returns(uint){return ++a;}
}
contract B is A {}
contract C is A {}
"""
    results = analyze(tmp_path, compiler, source, IRRepeatedModifier)
    assert len(results) == 1


@pytest.mark.parametrize(
    "source,expected",
    [
        (
            "contract A {uint x; constructor(){x=42;} function f() internal view virtual returns(uint){return 0;}} contract B is A {uint y=f(); function f() internal view override returns(uint){return x;}}",
            1,
        ),
        (
            "contract A {uint x; constructor(){x=42;} function f() internal view virtual returns(uint){return x;}} contract B is A {uint y=f(); function f() internal pure override returns(uint){return 0;}}",
            0,
        ),
        (
            "contract A {uint x; constructor(){x=42;}} contract B is A {uint y=first(); function first() internal view returns(uint){return x==0?second():x;} function second() internal view returns(uint){return first();}}",
            1,
        ),
        (
            "contract A {uint x; modifier m(){x=42;_;} constructor() m {}} contract B is A {uint y=x;}",
            1,
        ),
    ],
)
def test_initializer_call_context(tmp_path, compiler, source, expected):
    assert len(analyze(tmp_path, compiler, source, IRConstructorOrder)) == expected


def test_sibling_initializer_dispatch(tmp_path, compiler):
    source = """
contract A {uint internal x; constructor(){x=42;}}
contract B is A {
 uint public y=f();
 function f() internal view virtual returns(uint){return 0;}
}
contract C is B {function f() internal view override returns(uint){return x;}}
contract D is B {function f() internal pure override returns(uint){return 0;}}
"""
    results = analyze(tmp_path, compiler, source, IRConstructorOrder)
    assert len(results) == 1
    assert "in C " in results[0]["description"]


@pytest.mark.parametrize("version", ["0.4.25", "0.5.16", "0.6.11", "0.7.6"])
def test_legacy_sources(tmp_path, solc_binary_path, version):
    target = tmp_path / "Legacy.sol"
    target.write_text("""
pragma solidity >=0.4.22;
contract A {uint internal x; constructor() public {x=42;}}
contract B is A {uint public y=x;}
contract C {
 modifier twice(){_;_;}
 function f(uint a) public pure twice returns(uint){return ++a;}
}
""")
    slither = Slither(str(target), solc=solc_binary_path(version))
    slither.register_detector(IRConstructorOrder)
    slither.register_detector(IRRepeatedModifier)
    assert [len(results) for results in slither.run_detectors()] == [1, 1]
