from overlay.transform import outline_all_conditionals
from slither import Slither
from overlay.ast.graph import OverlayGraph

def print_test_by_name(name: str):
    slither = Slither(name + '.sol')
    graph = OverlayGraph(slither)
    outline_all_conditionals(graph)
    with open(name + '.out') as f:
        assert graph.to_text_repr() == f.read()


def test_fib_rec():
    print_test_by_name('fib_rec')

def test_fib_itr():
    print_test_by_name('fib_itr')

def test_simple_if():
    print_test_by_name('simple_if')

def test_simple_while():
    print_test_by_name('simple_while')

def test_simple_for():
    print_test_by_name('simple_for')

def test_simple_while_with_break():
    print_test_by_name('simple_while_with_break')

def test_simple_do_while():
    print_test_by_name('simple_do_while')

def test_compound_if_while():
    print_test_by_name('compound_if_while')

def test_compound_if_while_break():
    print_test_by_name('compound_if_while_break')

def test_simple_ternary():
    print_test_by_name('simple_ternary')