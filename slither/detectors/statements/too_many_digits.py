"""
Module detecting numbers with too many digits.
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

class TooManyDigits(AbstractDetector):
    """
    Detect numbers with too many digits
    """

    ARGUMENT = 'too_many_digits'  # slither will launch the detector with slither.py --too_many_digits
    HELP = 'Numbers with too many digits (human readability risk)'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/ethereum/web3.js/blob/0.15.0/lib/utils/utils.js'
    WIKI_TITLE = 'too_many_digits'
    WIKI_DESCRIPTION = 'Plugin too_many_digits'
    WIKI_EXPLOIT_SCENARIO = 'An error or malicious intent may have caused a number with many digits to be different than the number originally intended. This kind of error is usually difficult to find visually.'
    WIKI_RECOMMENDATION = 'The number used in the contract has too many digits. Try to use an Ether denomination instead'

    def _detect(self):
        results = []

        from slither import Slither
        from slither.slithir.variables import Constant

        # iterate over all contracts
        for contract in self.slither.contracts_derived:
        # iterate over all functions
            for f in contract.functions:
                # iterate over all the nodes
                for node in f.nodes:
                    # each node contains a list of IR instruction
                    for ir in node.irs:
                        # iterate over all the variables read by the IR 
                        for read in ir.read:
                            # if the variable is a constant
                            if isinstance(read, Constant):
                                # read.value can return an int or a str. Convert it to str
                                value_as_str = str(read.value)
                                #name_as_str = str(read.name)
                                line_of_code = str(node.expression)
                                if '00000' in value_as_str:
                                    # Info to be printed
                                    info = 'In {}.{} ({}), too many digits used in expression:\n\t- {}\n\tPlease use the proper Ether denomination instead\n'
                                    info = info.format(contract.name, f.name, f.source_mapping_str, line_of_code)

                                    # Add the result in result
                                    json = self.generate_json_result(info)
                                    self.add_function_to_json(f, json)
                                    results.append(json)
        return results
