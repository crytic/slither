from abc import ABC, abstractmethod

class Dataflow(ABC):

    @abstractmethod
    def _merge_fathers(self, node):
        pass

    @abstractmethod
    def _is_fix_point(self, node, values):
        pass

    @abstractmethod
    def _transfer_function(self, node, values):
        pass

    @abstractmethod
    def _store_values(self, node, values):
        pass

    @abstractmethod
    def _filter_sons(self, node):
        pass

    @abstractmethod
    def _update_result(self, node, values):
        pass

    @abstractmethod
    def result(self):
        pass

    def explore(self, node, visited):
        if node in visited:
            return

        visited = visited + [node]

        values = self._merge_fathers(node)

        if self._is_fix_point(node, values):
            return

        values = self._transfer_function(node, values)

        self._store_values(node, values)

        sons = self._filter_sons(node)
        for son in sons:
            self.explore(son, visited)
