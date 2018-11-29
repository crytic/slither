"""
Module detecting constant functions
Recursively check the called functions
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class ConstantFunctions(AbstractDetector):
    """
    Constant function detector
    """

    ARGUMENT = 'constant-function'  # run the detector with slither.py --ARGUMENT
    HELP = 'Constant functions changing the state'  # help information
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#constant-functions-changing-the-state'

    def detect(self):
        """ Detect the constant function changing the state

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func','#varsWritten'}
        """
        results = []
        for c in self.contracts:
            for f in c.functions:
                if f.contract != c:
                    continue
                if f.view or f.pure:
                    if f.contains_assembly:
                        attr = 'view' if f.view else 'pure'
                        info = '{}.{} ({}) is declared {} but contains assembly code\n'
                        info = info.format(f.contract.name, f.name, f.source_mapping_str, attr)
                        self.log(info)
                        sourceMapping = [f.source_mapping]
                        results.append({'check':self.ARGUMENT,
                                        'function':{'name': f.name, 'source_mapping': f.source_mapping},
                                        'contains_assembly': True,
                                        'variables': []})

                    variables_written = f.all_state_variables_written()
                    if variables_written:
                        attr = 'view' if f.view else 'pure'
                        info = '{}.{} ({}) is declared {} but changes state variables:\n'
                        info = info.format(f.contract.name, f.name, f.source_mapping_str, attr)
                        for variable_written in variables_written:
                            info += '\t- {}.{}\n'.format(variable_written.contract.name,
                                                       variable_written.name)
                        self.log(info)

                        results.append({'check':self.ARGUMENT,
                                        'function':{'name': f.name, 'source_mapping': f.source_mapping},
                                        'variables': [{'name': v.name,
                                                       'source_mapping': v.source_mapping}
                                                      for v in variables_written],
                                        'contains_assembly': False})
        return results
