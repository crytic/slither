"""
Gas: Module detecting Array length inside of loop

"""

from slither import solc_parsing
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

class GasInefficientLoopLength(AbstractDetector):
    """
    Gas: Array length inside of loop
    """

    ARGUMENT = "gas-length-within-for-loop"
    HELP = "Gas Inefficiencies Detected"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#caching-the-length-in-for-loops"
    WIKI_TITLE = "Caching the length in for loops"
    WIKI_DESCRIPTION = "Reading array length at each iteration of the loop takes 6 gas" 
    
    def _detect(self):
        results = []
        for contract in self.contracts:
            contract_source_code = contract.source_code
            ast = solc_parsing.compile_source(contract_source_code)['<stdin>:{}'.format(contract.name)]['ast']
            for function_ast in ast['functions']:
                if function_ast['type'] == 'FunctionDefinition':
                    function_name = function_ast['name']
                    for statement in function_ast['body']['statements']:
                        if statement['type'] == 'ForStatement':
                            for_variable = statement['init']['names'][0]['id']['name']
                            for_body_ast = statement['body']['statements']
                            for body_statement in for_body_ast:
                                if body_statement['type'] == 'ExpressionStatement':
                                    body_expression = body_statement['expression']
                                    if body_expression['type'] == 'MemberAccess':
                                        if body_expression['expression']['type'] == 'Identifier' and body_expression['expression']['name'] == for_variable and body_expression['memberName'] == 'length':
                                            results.append({
                                                "contract": contract.name,
                                                "function": function_name,
                                                "line": body_statement['src']['line'],
                                                "variable": for_variable
                                            })
        return results
