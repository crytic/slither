
class ChildNode(object):
    def __init__(self):
        super(ChildNode, self).__init__()
        self._node = None

    def set_node(self, node):
        self._node = node

    @property
    def node(self):
        return self._node

    @property
    def function(self):
        return self.node.function

    @property
    def contract(self):
        return self.node.function.contract

    @property
    def slither(self):
        return self.contract.slither