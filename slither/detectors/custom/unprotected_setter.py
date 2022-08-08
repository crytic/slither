from slither.core.cfg.node import NodeType

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class UnprotectedSetter(AbstractDetector):
    """
    Sees if contract contains a setter, that changes contract paramater without modifier protection or access control inside the function
    """

    ARGUMENT = 'unprotected-setter' # slither will launch the detector with slither.py --detect mydetector
    HELP = 'Contract parameter might be changed be anyone'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://workflowy.com/s/40d940743275/G8dJAU9ahhPNuSCY#/c9183b987c7f'
    WIKI_TITLE = 'Unprotected Setter'
    WIKI_DESCRIPTION = "Почти всегда setter'ы должны быть защищены какой-то ролью"
    WIKI_EXPLOIT_SCENARIO = 'Кто угодно может менять параметры протокола'
    WIKI_RECOMMENDATION = 'Add access control'


    def is_setter(self, fun, params=None):

        if not params:
            params = fun.parameters # параметры функции

        for n in fun.nodes: # в первом приближении нода это строчка
            if(n.type==NodeType.EXPRESSION):
                for v in n.state_variables_written:
                    lr = str(n.expression).split(' = ')
                    if len(lr)>1:
                        for p in params:
                            if '.' in lr[0]: continue
                            if '[' in lr[0]: continue
                            if lr[1]==str(p): return lr[0] # присваеваем аргумент функции напрямую в сторадж

        # TODO: непрямые присваивания
        return None

    def has_access_control(self, fun):

        for m in fun.modifiers:
            for m.name in ['initializer', 'onlyOwner']:
                return True;

        if fun.visibility in ['internal','private']:
            return False;

        # или msg.sender внутри функции сверяется напрямую в require
        # for n in fun.nodes:
        #     for c in n.internal_calls:
        #         if c.name in ['require(bool,string)', 'require(bool)']:
        #             print(n.expression)

        return fun.is_protected();

    def _detect(self):

        res = []

        for contract in self.compilation_unit.contracts_derived:
            for f in contract.functions:
                if not self.has_access_control(f):
                    x = self.is_setter(f)
                    if (x!= None):
                        # print()
                        res.append(self.generate_result([
                            f.contract_declarer.name, ' ',
                            f.name, ' is a non-protected setter ',
                            x, ' is written'
                            '\n']))


        return res