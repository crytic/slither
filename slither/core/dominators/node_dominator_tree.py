'''
    Nodes of the dominator tree
'''

from slither.core.children.child_function import ChildFunction

class DominatorNode(object):

    def __init__(self):
        self._succ = set()
        self._nodes = []

    def add_node(self, node):
        self._nodes.append(node)

    def add_successor(self, succ):
        self._succ.add(succ)

    @property
    def cfg_nodes(self):
        return self._nodes

    @property
    def sucessors(self):
        '''
            Returns:
                dict(Node)
        '''
        return self._succ

class DominatorTree(ChildFunction):

    def __init__(self, entry_point):
        super(DominatorTree, self).__init__()
        

        
