"""
Module detecting constant functions
Recursively check the called functions
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.formatters.attributes.const_functions import format


class ConstantFunctionsAsm(AbstractDetector):
    """
    Constant function detector
    """

    ARGUMENT = 'constant-function-asm'  # run the detector with slither.py --ARGUMENT
    HELP = 'Constant functions using assembly code'  # help information
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#constant-functions-using-assembly-code'

    WIKI_TITLE = 'Constant functions using assembly code'
    WIKI_DESCRIPTION = '''
Functions declared as `constant`/`pure`/`view` using assembly code.

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
        """ Detect the constant function using assembly code

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func','#varsWritten'}
        """
        results = []
        if self.slither.solc_version and self.slither.solc_version >= "0.5.0":
            return results
        for c in self.contracts:
            for f in c.functions:
                if f.contract_declarer != c:
                    continue
                if f.view or f.pure:
                    if f.contains_assembly:
                        attr = 'view' if f.view else 'pure'

                        info = [f, f' is declared {attr} but contains assembly code\n']
                        res = self.generate_result(info, {'contains_assembly': True})

                        results.append(res)

        return results

    @staticmethod
    def _format(slither, result):
        format(slither, result)
