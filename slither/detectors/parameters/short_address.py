from slither.core.solidity_types.elementary_type import ElementaryType, Uint, Int
from slither.detectors.abstract_detector import AbstractDetector,DetectorClassification
from slither.slithir.operations import Length


class ShortAddress(AbstractDetector):
    ARGUMENT = "short-address"
    HELP = "Short Address"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#short-address"

    WIKI_TITLE = "Short Address"
    WIKI_DESCRIPTION = "This function does not check the length of the data, so it may be attacked by a short address."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity

    function sendCoin(address to, uint amount) returns(bool sufficient) {
         if (balances[msg.sender] < amount) return false;
         balances[msg.sender] -= amount;
         balances[to] += amount;
         Transfer(msg.sender, to, amount);
         return true;
     }
```
If the length of the address is less than 32 bits, the subsequent data is used to make up the 32 bits. 
If `amount` is 2, but length of `to` lost 2 bits, this contract will transfer 512 instead 2.
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "check the length of the `msg.data`"
    )


    def  check_length_with_modifier(self, modifier):
        for node in modifier.nodes:
            if node.contains_if() or node.contains_require_or_assert():
                for ir in node.irs:
                    if isinstance(ir, Length) and ir.value.name == "msg.data":
                        return True
        return False


    def isnt_check_length(self, function,  modifier_with_msgData):
        if function.modifiers:
            matched_modifiers = [m for m in function.modifiers if m in modifier_with_msgData]
            if matched_modifiers:
                return False

        for node in function.nodes:
            for ir in node.irs:
                if isinstance(ir, Length) and ir.value.name == "msg.data":
                    return False
        return True


    # pylint: disable=too-many-nested-blocks,too-many-branches
    def detect_address(self, contract):
        modifier_with_msgData = []
        res = []

        for modifier in contract.modifiers:
            if self.check_length_with_modifier(modifier):
                modifier_with_msgData += [modifier]
                
        for function in contract.functions_declared:
            if not function.nodes:
                continue

            if function.is_constructor:
                continue

            is_addr_func = False
            is_int_func = False

            if function.parameters:
                for v in function.parameters:
                    if not isinstance(v.type, ElementaryType):
                        continue

                    if v.type == ElementaryType("address"):
                        is_addr_func = True

                    elif is_addr_func and v.type.name in Uint+Int:
                        is_int_func = True
                    
            if is_addr_func and is_int_func:
                if self.isnt_check_length(function,  modifier_with_msgData):
                    res += [function]

        return res
        

    def _detect(self):
        results = []
        for contract in self.contracts:
            functions = self.detect_address(contract)

            if functions:
                for function in functions:
                    info = [function, " can be used to launch short address attack.", "\n",]
                    
                    json = self.generate_result(info)
                    results.append(json)

        return results
