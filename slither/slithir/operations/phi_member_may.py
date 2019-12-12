from .phi import Phi
from slither.utils.colors import green


class PhiMemberMay(Phi):

    def __init__(self, left_variable, base, nodes, phi_info):
        super(PhiMemberMay, self).__init__(left_variable, nodes)
        self._phi_info = phi_info
        self._base = base

    @property
    def phi_info(self):
        return self._phi_info

    @property
    def base(self):
        return self._base

    @property
    def read(self):
        raise Exception('Not implemented')

    def __str__(self):
        txt = []
        for key, item in self.phi_info.items():
            # items_txt = [f'{item}' for item in items]
            # txt.append(f'\t\t\t\t\t{key} :-> {items_txt}')
            txt = [f'{key} :-> {item}']
        txt = ', '.join(txt)

        return green(f'{self.lvalue}({self.lvalue.type}) := \u03D5May({self.base}:{txt})')
