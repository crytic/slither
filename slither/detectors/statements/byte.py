from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class ArrayOfByte(AbstractDetector):

    ARGUMENT = "byte"
    HELP = "Array of bytes"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#byte"

    WIKI_TITLE = "Byte[]"
    WIKI_DESCRIPTION = "The type byte[] is an array of bytes, but due to padding rules, it wastes 31 bytes of space for each element (except in storage)."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//from JiuZhou

contract waste{
	byte[] private _secret;
	constructor() public{
		_secret = new byte[](8);
	}
}

contract Nowaste{
	bytes private _secret;
	constructor() public{
	}
}
```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = " It is better to use the bytes type instead."

    @staticmethod
    def detect_array_of_byte(contract):
        ret = []

        for v in contract.variables:
            flag = True
            type = str(v.type)
            if 'byte' in type:
                if 'bytes' != type:
                    ret.append(v)
                

        return ret

    def _detect(self):
        """"""
        results = []
        for c in self.compilation_unit.contracts_derived:
            values = self.detect_array_of_byte(c)
            
            if not values:
                continue

            info = ["Description:It wastes many space for each element.\n",]
            info += ["Contract:", c, "\n"]
            for var in values:

                info += ["\t- ", var, "\n",]

            res = self.generate_result(info)
            results.append(res)

        return results
