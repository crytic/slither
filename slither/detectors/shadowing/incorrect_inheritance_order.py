from collections import defaultdict
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

def detect_wrong_inheritance_order(contract, tuples):
    res = []
    const_inherit = []
    for inherit in contract.immediate_inheritance:
        const_inherit += [[inherit] + [c for c in inherit.inheritance]]
    
    for t in tuples:
        value_inherit = defaultdict(list)

        tuples[t].sort(reverse=True, key=lambda x: x.source_mapping['lines'][0])

        value_tmp = None
        value_id = -1
        for value in tuples[t]:
            if t[1]== 0:
                contract_declarer = value.contract
            else:
                contract_declarer = value.contract_declarer

            flag = None
            for i in range(len(const_inherit)):
                if contract_declarer in const_inherit[i]:
                   value_inherit[i].append(value)
                
                else:
                    if flag == False and len(value_inherit[i]) > 0:
                        flag = True
                    continue
                
                if flag == None and len(value_inherit[i]) > 1:
                    flag = True

                elif flag == False and len(value_inherit[i]) > 1:
                    flag = True
                    value_tmp = None
                    value_id = -1

                elif flag == True and len(value_inherit[i]) == 1:
                    if i > value_id:
                        flag = False
                        value_id = i
                        value_tmp = value
        
        if value_tmp != None:
            res.append(value_tmp)

    return res


def detect_functions(contract, functions):
    funcs = defaultdict(list)
    
    for f in functions:
        if f.visibility == "private": 
            continue

        if f.is_constructor_variables:
            continue
        
        f_tuple = (f.name, tuple(f.signature[1]))
        
        #inheritance functions
        if f.contract_declarer != contract:
            funcs[f_tuple].append(f)

        #original functions
        elif f_tuple in funcs:
            funcs.pop(f_tuple)

    return funcs


def detect_variables(contract):
    vars = defaultdict(list)
    vars_inherit = defaultdict(list)
    vars_declared = []

    for v in contract.state_variables_declared:
        vars_declared.append(v.name)
        
    for c in contract.immediate_inheritance:
        for v in c.variables:
            if v.name in vars_declared:
                continue
            
            if (v.contract, v) in vars_inherit[v.name]:
                continue

            vars_inherit[v.name].append((v.contract, v))
    
    for key in vars_inherit:
        if len(vars_inherit[key]) > 1:
            for (c, v) in vars_inherit[key]:
                vars[(key, 0)].append(v)

    return vars


def detect_inheritance(contract):
    functions = contract.functions
    modifiers = contract.modifiers

    res = { **detect_functions(contract, functions), 
            **detect_functions(contract, modifiers), 
            **detect_variables(contract)
        }

    res = detect_wrong_inheritance_order(contract, res)
    return res


class IncorrectInheritanceOrder(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = 'inheritance-order' # slither will launch the detector with slither.py --detect mydetector
    HELP = 'Incorrect inheritance order'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    # region wiki
    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect_inheritance_order'
    WIKI_TITLE = 'Incorrect inheritance order'
    WIKI_DESCRIPTION = 'The wrong inheritance sequence will result in the functionality of the contract not being what the developer expected'
    WIKI_EXPLOIT_SCENARIO = """
```solidity


```
"""
    WIKI_RECOMMENDATION = 'correct inheritance order'
    # endregion wiki

    def _detect(self):
        f_results = []
        record_tuple = []
        results = []
        for contract in self.contracts:
            
            if len(contract.immediate_inheritance) > 1:
                f_results = detect_inheritance(contract)

            if f_results:
                info = [
                        contract,
                        "Wrong inheritance order will result in the functionality of the contract not being what the developer expected.\n",
                    ]

                for name in f_results:
                    info += ["\t-", name, "\n"]

                res = self.generate_result(info)
                results.append(res)

            record_tuple += f_results

        return results
