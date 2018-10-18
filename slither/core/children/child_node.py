
class ChildNode(object):
    def __init__(self):
        super(ChildNode, self).__init__()
        self._node = None

    def set_node(self, node):
        self._node = node

    @property
    def node(self):
        return self._node
