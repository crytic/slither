import pickle
from typing import Dict

from slither.tools.middle.framework.var import SymVar


class InconsistentStateError(Exception):
    """
    An Exception to be raised when the user leads the engine to a state in which
    we get an inconsistent execution state.
    """
    pass


class UnionFindSymVar:
    """
    Implements the Union-Find algorithm on SymVars.
    """
    # Maps each SymVar to its parent
    parent = Dict[SymVar, SymVar]

    def __init__(self):
        self.parent = {}

    def make_set(self, symvar: SymVar):
        if symvar not in self.parent:
            self.parent[symvar] = symvar

    def find(self, symvar: SymVar):
        current = symvar
        while self.parent[current] != current:
            current = self.parent[current]
        # Compress the path from symvar to the representative node
        self.parent[symvar] = current
        return current

    def union(self, a: SymVar, b: SymVar):
        a_rep = self.find(a)
        b_rep = self.find(b)

        # A becomes a child of B
        self.parent[a_rep] = b_rep

    def find_union(self, a: SymVar):
        a_rep = self.find(a)
        union = {a_rep}
        q = [k for k in self.parent.keys() if self.parent[k] in union and k not in union]
        while q:
            union.update(q)
            q = [k for k in self.parent.keys() if self.parent[k] in union and k not in union]
        return list(union)


def pickle_object(obj, filename):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def unpickle_object(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)
