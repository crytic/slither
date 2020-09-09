import sys

try:
    from graphviz import Digraph as _Digraph
except ImportError:
    print("ERROR: in order to use middle, you need to install graphviz")
    print("pip3 install graphviz\n")
    sys.exit(-1)

Digraph = _Digraph
