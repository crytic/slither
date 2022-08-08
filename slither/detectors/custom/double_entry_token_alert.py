from slither.core.cfg.node import NodeType

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class DoubleEntryAlert(AbstractDetector):
    """
    Sees if contract contains a function wich is vulnurable to double-entry tokens attack
    """

    ARGUMENT = 'double-entry-token-alert' # slither will launch the detector with slither.py --detect mydetector
    HELP = 'The function might be sensitive to double entry token usage'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.LOW

    WIKI = 'https://docs.google.com/presentation/d/1jbOBBou-6eUBzm32X8cflTl4V6xvFd8jdaIZmi1A7kM/edit#slide=id.g142209ff0ae_0_0'
    WIKI_TITLE = 'Double-entry token'
    WIKI_DESCRIPTION = "Возможны проблемы при использования double-entry токена"
    WIKI_EXPLOIT_SCENARIO = '...'
    WIKI_RECOMMENDATION = 'Контракт не должен обрабатывать случай, когда два адреса указывают на один токен'


    def get_tokens_as_params(self, fun):

        res = []  # параметры функции

        for p in fun.parameters:
            if str(p.type) in ['IERC20[]', 'address[]']:
                res.append(p)

        return res

    def do_have_token_interaction(self, fun, token):

        for n in fun.nodes:
            if str(token) in str(n.expression):
                if '.transfer' in str(n.expression): return True
                if '.balanceOf' in str(n.expression): return True

        return False

    def _detect(self):

        res = []

        for contract in self.compilation_unit.contracts_derived:
            for f in contract.functions:

                tokens = self.get_tokens_as_params(f)

                if len(tokens)>0:
                    for t in tokens:
                        if self.do_have_token_interaction(f, t):
                            res.append(self.generate_result([
                                f.contract_declarer.name, ' ',
                                f, ' might be vulnerauble to double-entry token exploit',
                                '\n']))

        return res