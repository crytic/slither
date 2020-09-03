from .operation import Operation


class Nop(Operation):
    @property
    def read(self):
        return []

    @property
    def used(self):
        return []

    def __str__(self):
        return "NOP"
