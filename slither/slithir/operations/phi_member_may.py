from .phi import Phi
from slither.utils.colors import green


class PhiMemberMay(Phi):

    def __init__(self, left_variable, nodes, phi_info):
        super(PhiMemberMay, self).__init__(left_variable, nodes)
        self._phi_info = phi_info

    @property
    def phi_info(self):
        return self._phi_info

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

        return green('{}({}) := \u03D5May({})'.format(self.lvalue,
                                                      self.lvalue.type,
                                                      txt))
