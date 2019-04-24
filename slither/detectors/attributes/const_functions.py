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

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#constant-functions-changing-the-state'

    WIKI_TITLE = 'Constant functions changing the state'
    WIKI_DESCRIPTION = '''
Functions declared as `constant`/`pure`/`view` changing the state or using assembly code.

`constant`/`pure`/`view` was not enforced prior Solidity 0.5.
Starting from Solidity 0.5, a call to a `constant`/`pure`/`view` function uses the `STATICCALL` opcode, which reverts in case of state modification.

As a result, a call to an [incorrectly labeled function may trap a contract compiled with Solidity 0.5](https://solidity.readthedocs.io/en/develop/050-breaking-changes.html#interoperability-with-older-contracts).'''

    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract Constant{
    uint counter;
    function get() public view returns(uint){
       counter = counter +1;
       return counter
    }
}
```
`Constant` was deployed with Solidity 0.4.25. Bob writes a smart contract interacting with `Constant` in Solidity 0.5.0. 
All the calls to `get` revert, breaking Bob's smart contract execution.'''

    WIKI_RECOMMENDATION = 'Ensure that the attributes of contracts compiled prior to Solidity 0.5.0 are correct.'

    def _detect(self):
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
                        json = self.generate_json_result(info)
                        self.add_function_to_json(f, json)
                        json['elements'].append({'type': 'info',
                                                 'contains_assembly' : True})
                        results.append(json)

                    variables_written = f.all_state_variables_written()
                    if variables_written:
                        attr = 'view' if f.view else 'pure'
                        info = '{}.{} ({}) is declared {} but changes state variables:\n'
                        info = info.format(f.contract.name, f.name, f.source_mapping_str, attr)
                        for variable_written in variables_written:
                            info += '\t- {}.{}\n'.format(variable_written.contract.name,
                                                         variable_written.name)


                        json = self.generate_json_result(info)
                        self.add_function_to_json(f, json)
                        self.add_variables_to_json(variables_written, json)
                        json['elements'].append({'type': 'info',
                                                  'contains_assembly' : False})
                        results.append(json)

        return results
