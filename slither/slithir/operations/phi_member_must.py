from .phi_member_may import PhiMemberMay
from slither.utils.colors import green


class PhiMemberMust(PhiMemberMay):
    def __str__(self):
        txt = []
        for key, item in self.phi_info.items():
            txt = [f"{key} :-> {item}"]
        txt = ", ".join(txt)

        return green(f"{self.lvalue}({self.lvalue.type}) := \u03D5Must({self.base}:{txt})")
