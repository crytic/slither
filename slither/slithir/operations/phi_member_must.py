
from .phi_member_may import PhiMemberMay
from slither.utils.colors import green

class PhiMemberMust(PhiMemberMay):

    def __str__(self):

        txt = []
        for key, item in self.phi_info.items():
            #items_txt = [f'{item}' for item in items]
            #txt.append(f'\t\t\t\t\t{key} :-> {items_txt}')
            txt = [f'{key} :-> {item}']
        txt = ', '.join(txt)

        return green('{}({}) := \u03D5Must({})'.format(self.lvalue,
                                                   self.lvalue.type,
                                                   txt))
