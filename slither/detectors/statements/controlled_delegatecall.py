from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import LowLevelCall
from slither.analyses.taint.all_variables import is_tainted

class ControlledDelegateCall(AbstractDetector):
    """
    """

    ARGUMENT = 'controlled-delegatecall'
    HELP = 'Controlled delegatecall destination'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#controlled-delegatecall'

    def controlled_delegatecall(self, function):
        ret = []
        for node in function.nodes:
            for ir in node.irs:
                if isinstance(ir, LowLevelCall) and ir.function_name in ['delegatecall', 'codecall']:
                    if is_tainted(self.slither, ir.destination):
                        ret.append(node)
        return ret

    def detect(self):
        results = []

        for contract in self.slither.contracts:
            for f in contract.functions:
                if f.contract != contract:
                    continue
                nodes = self.controlled_delegatecall(f)
                if nodes:
                    info = '{}.{} ({}) uses delegatecall to a input-controlled function id\n'
                    info = info.format(contract.name, f.name, f.source_mapping_str)
                    for node in nodes:
                        info += '\t{} ({})\n'.format(node.expression, node.source_mapping_str)
                    self.log(info)

                    results.append({'check':self.ARGUMENT,
                                    'function':{
                                        'name': f.name,
                                        'source_mapping': f.source_mapping},
                                    'controlled_delegatecalls': [
                                        {'expression': str(node.expression),
                                         'source_mapping':node.source_mapping} for node in nodes]})
        return results
