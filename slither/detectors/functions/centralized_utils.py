# -*- coding:utf-8 -*-
import time
from slither.core.declarations import FunctionContract, SolidityVariableComposed, Modifier
from slither.core.expressions import CallExpression
import json
from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.core.expressions import CallExpression
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import NodeType
from slither.core.declarations import (
    Contract,
    Pragma,
    Import,
    Function,
    Modifier,
)
from slither.core.declarations.event import Event
from slither.core.declarations import FunctionContract, Modifier
from slither.core.declarations import (
    SolidityFunction,
)
from slither.core.solidity_types.elementary_type import ElementaryType

from slither.slithir.operations import SolidityCall, InternalCall
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.index import Index
from slither.slithir.operations.binary import BinaryType
from slither.slithir.operations.send import Send
from slither.slithir.operations.transfer import Transfer
from slither.detectors.functions.modifier_utils import ModifierUtil

class CentralizedUtil:

    openzeppelin_contracts = [
        ('AccessControl','mapping(bytes32 => RoleData)','_roles'),
        ('AccessControl','mapping(bytes32 => AccessControl.RoleData)','_roles'),
        ('AccessControlEnumerable','mapping(bytes32 => EnumerableSet.AddressSet)','_roleMembers'),
        ('Ownable','address','_owner'),
        ('AccessControlUpgradeable','mapping(bytes32 => RoleData)','_roles'),
        ('AccessControlUpgradeable','mapping(bytes32 => AccessControlUpgradeable.RoleData)','_roles'),
        ('AccessControlEnumerableUpgradeable','mapping(bytes32 => EnumerableSetUpgradeable.AddressSet)','_roleMembers'),
        ('OwnableUpgradeable','address','_owner'),
        ('Pausable','bool','_paused'),
        ('PausableUpgradeable','bool','_paused'),
    ]
    openzeppelin_modifiers=[
        'onlyowner','onlyrole','whennotpaused','whenpaused','onlyadmin','only'
    ]

    @staticmethod
    def detect_inheritance(c: Contract):
        '''
        Detects whether the contract inherits from contracts in OpenZeppelin and returns the variables used.
        '''
        inheritance = c.inheritance
        oz_var_usage = {}
        oz_inheritance = [
            oz_contract
            for c in inheritance
                for oz_contract in CentralizedUtil.openzeppelin_contracts
                    if c.name == oz_contract[0]
        ]
        # Check for usage of variables defined in OpenZeppelin contracts and add them to oz_var_usage
        for oz in oz_inheritance:
            for svar in c.all_state_variables_read + c.all_state_variables_written:
                if str(svar.type) == oz[1] and svar.name == oz[2]:
                    oz_var_usage[svar] = {'var_name':svar.name,'contract_name': oz[0], 'var_type': oz[1]}
        return oz_var_usage
    
    @staticmethod
    def detect_function_oz_usage(function:Function,oz_var_usage):
        '''
        Detects the usage or writing of variables from OpenZeppelin within a function.
        '''
        ret_function_read_or_write=[]
        ret_function_write=[]
        # Functions using variables from OpenZeppelin might have centralized restrictions
        for var in function.state_variables_read+function.state_variables_written:
            if var in oz_var_usage.keys() and var not in ret_function_read_or_write:
                ret_function_read_or_write.append({var:oz_var_usage[var]})
        return ret_function_read_or_write

    @staticmethod
    def detect_modifiers_common(contract:Contract):
        '''
        Detects the usage of common modifiers (typically from OpenZeppelin) in the contract.
        '''
        ret=[]
        for m in contract.modifiers:
            # Check if the modifier name matches any in openzeppelin_modifiers after processing
            for om in CentralizedUtil.openzeppelin_modifiers:
                if str(m.name).lower().replace('_','') == om or str(m.name).lower() == om or om in str(m.name).lower() or om in str(m.name).lower().replace('_',''):
                    # Find state variable reads within this modifier
                    ret.append({om:{'modifier':m}})
        return ret
    
    @staticmethod
    def check_modifier_if_read_state_variable(modifier:Modifier):
        '''
        Checks if the modifier reads state variables.
        '''
        ret=[]
        # Recursively find all calls within the modifier and its subcalls
        def find_calls(modifier:Modifier):
            ret=[]
            for call in modifier.calls:
                if call.node_type == NodeType.MODIFIER:
                    ret.append(call)
                    ret+=find_calls(call)
            return ret
        return ret
    
    @staticmethod
    def detect_specific_modifier(contract:Contract):
        '''
        Detects the usage of user-defined modifiers (non-OpenZeppelin) in the contract.
        '''
        ret=[]
        # Iterate over all modifiers, excluding those in openzeppelin_modifiers, similar to how detect_modifiers_common works
        for m in contract.modifiers:
            
            for om in CentralizedUtil.openzeppelin_modifiers:
                if not (str(m.name).lower().replace('_','') == om or str(m.name).lower() == om):
                    # Find state variables read or written within this modifier, specifically for address types
                    for var in m.state_variables_read+m.state_variables_written:
                        if var.type == ElementaryType('address') and var not in ret:
                            ret.append({var:{'var_name':var.name,'modifier':m,'var_type':var.type}})
                    for var in m.variables_read:
                        if hasattr(var,"type") and var.type == ElementaryType('address') and var.name=='msg.sender' and var not in ret:
                            ret.append({var:{'var_name':var.name,'modifier':m,'var_type':var.type}})
        return ret

    @staticmethod
    def detect_function_if_centralized(function:Function):
        ret=[]
        # A special modifier 'whennotpaused' might not necessarily denote a centralized function if it's unrelated to pausing operations
        if 'whennotpaused' in [str(m.name).lower() for m in function.modifiers] and \
            'pause' not in function.name.lower():
            return ret
        
        oz_var_usage = CentralizedUtil.detect_inheritance(function.contract)
        oz_read_or_written=CentralizedUtil.detect_function_oz_usage(function,oz_var_usage)
        function_modifier_info=[]
        contract_common_modifiers_info=CentralizedUtil.detect_modifiers_common(function.contract)
        contract_specific_modifiers_info=CentralizedUtil.detect_specific_modifier(function.contract)
        function_unmodifier_check=CentralizedUtil.detect_function_unmodifier_check(function)
        for info in contract_common_modifiers_info:
            for om in info.keys():
                if info[om]['modifier'] in function.modifiers and info not in function_modifier_info:
                    function_modifier_info.append(info)
        for info in contract_specific_modifiers_info:
            for var in info.keys():
                if info[var]['modifier'] in function.modifiers and info not in function_modifier_info:
                    function_modifier_info.append(info)
        for info in function_unmodifier_check:
            for var in info.keys():
                if info not in function_modifier_info:
                    function_modifier_info.append(info)
        if oz_read_or_written or function_modifier_info:
            ret.append({'function':function,'oz_read_or_written':oz_read_or_written,'function_modifier_info':function_modifier_info})
        return ret
    
    @staticmethod
    def detect_function_unmodifier_check(function: Function):
        ret = []

        def process_statement(s):
            """Processes statements to extract relevant information."""
            for var in s.state_variables_read:
                ret.append({var: {'var_name': var.name, 'node': s, 'var_type': var.type}})

        for s in function.nodes:
            # Check for 'require' or 'IF', and 'msg.sender' or 'msgsender'
            if ('require' in str(s) or 'IF' in str(s)) and ("msg.sender" in str(s).lower() or "msgsender" in str(s).lower()):
                contains_msg_sender_call = False
                
                # Iterate over all calls within this statement
                for call in s.calls_as_expression:
                    if call.called and hasattr(call.called, "value") and isinstance(call.called.value, FunctionContract):
                        if any(isinstance(var, SolidityVariableComposed) for var in call.called.value.variables_read):
                            contains_msg_sender_call = True
                            break

                if contains_msg_sender_call or any(isinstance(vars_read, SolidityVariableComposed) for vars_read in s.variables_read):
                    process_statement(s)

        return ret

    @staticmethod
    def output_function_centralized_info(function: Function):
        info = {}
        
        info["function_name"] = function.name
        
        in_file = function.contract.source_mapping.filename.absolute
        # Retrieve the source code
        in_file_str = function.contract.compilation_unit.core.source_code[in_file]

        # Get the string
        start = function.source_mapping.start
        stop = start + function.source_mapping.length
        func_source = in_file_str[start:stop]
        
        info["function_source"] = func_source
        info["function_head"] = function.full_name

        address_vars_read = []
        for var in function.state_variables_read:
            if var.type == ElementaryType('address'):
                address_vars_read.append(var.name)
        info["address_vars_read"] = address_vars_read

        address_vars_read_in_modifiers = []
        for m in function.modifiers:
            for var in m.state_variables_read:
                if var.type == ElementaryType('address'):
                    address_vars_read_in_modifiers.append(var.name)
        info["address_vars_read_in_modifiers"] = address_vars_read_in_modifiers

        state_vars_written = []
        for var in function.state_variables_written:
            state_vars_written.append(var.name)
        info["state_vars_written"] = state_vars_written
        
        return info
    
    @staticmethod
    def detect_function_if_transfer(function:Function):
        for s in function.nodes:
            if 'set' in function.name.lower() or 'add' in function.name.lower():
                return False
            if 'call.value' in str(s) or 'transfer' in str(s) or 'send' in str(s):
                return True
        return False

    _function_risk_cache = {}
    @staticmethod
    def _get_cached_result(func, risk_type):
        if func in CentralizedUtil._function_risk_cache:
            return CentralizedUtil._function_risk_cache[func].get(risk_type)
        return None

    @staticmethod
    def _set_cached_result(func, risk_type, result):
        if func not in CentralizedUtil._function_risk_cache:
            CentralizedUtil._function_risk_cache[func] = {}
        CentralizedUtil._function_risk_cache[func][risk_type] = result

    @staticmethod
    def check_function_type_if_critical_risk(func:FunctionContract):
        cached_result = CentralizedUtil._get_cached_result(func, 'critical')
        if cached_result is not None:
            return cached_result

        for node in func.nodes:
            if any(isinstance(ir,Send) or isinstance(ir,Transfer) for ir in node.irs) or \
                'call.value' in str(node) or \
                'call{value' in str(node) or \
                any(hasattr(ir,'function_name') and str(ir.function_name).lower() in ['transferfrom','transfer'] for ir in node.irs):
                CentralizedUtil._set_cached_result(func, 'critical', True)
                return True

        CentralizedUtil._set_cached_result(func, 'critical', False)
        return False

    @staticmethod
    def check_if_state_vars_read_from_critical_risk(func:FunctionContract):
        cached_result = CentralizedUtil._get_cached_result(func, 'high')
        if cached_result is not None:
            return cached_result

        state_vars_in_critical=[]
        for f in func.contract.functions:
            if f is func:
                continue
            if CentralizedUtil.check_function_type_if_critical_risk(f):
                state_vars_in_critical.extend(f.state_variables_read)
        for var in state_vars_in_critical:
            if var in func.state_variables_written:
                CentralizedUtil._set_cached_result(func, 'high', True)
                return True

        CentralizedUtil._set_cached_result(func, 'high', False)
        return False

    @staticmethod
    def check_if_function_change_key_state(func:FunctionContract):
        cached_result = CentralizedUtil._get_cached_result(func, 'medium')
        if cached_result is not None:
            return cached_result

        if CentralizedUtil.check_if_state_vars_read_from_critical_risk(func) or \
           CentralizedUtil.check_function_type_if_critical_risk(func):
            CentralizedUtil._set_cached_result(func, 'medium', False)
            return False

        if len(func.state_variables_written) > 0:
            CentralizedUtil._set_cached_result(func, 'medium', True)
            return True

        CentralizedUtil._set_cached_result(func, 'medium', False)
        return False

    @staticmethod
    def check_if_function_other(func:FunctionContract):
        cached_result = CentralizedUtil._get_cached_result(func, 'low')
        if cached_result is not None:
            return cached_result

        if CentralizedUtil.check_if_state_vars_read_from_critical_risk(func) or \
           CentralizedUtil.check_function_type_if_critical_risk(func) or \
           CentralizedUtil.check_if_function_change_key_state(func):
            CentralizedUtil._set_cached_result(func, 'low', False)
            return False

        CentralizedUtil._set_cached_result(func, 'low', True)
        return True
