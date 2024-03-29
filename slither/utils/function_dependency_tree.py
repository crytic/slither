import copy
import itertools
from typing import List, Optional, Set
from falcon.core.cfg.node import Node

from falcon.core.declarations import Contract
from falcon.core.declarations.function import Function
from falcon.core.declarations.function_contract import FunctionContract
from falcon.core.declarations.solidity_variables import SolidityFunction

class FunctionUtil:
    def __init__(self, fn: FunctionContract):
        self.fn = fn 
        self.read = self.fn.all_state_variables_read()
        self.written = self.fn.all_state_variables_written()

    def is_rw(self, statevar):
        if not (statevar in self.read and statevar in self.written):
            return False  
        else:
            all_nodes = self.fn.all_nodes()
            processed = list()
            cur_node = self.fn.entry_point
            to_process = list()
            to_process.append(cur_node)
            while len(to_process)>0:
                node: Node = to_process.pop()
                if node in all_nodes and node not in processed:
                    read = node.state_variables_read
                    written = node.state_variables_written
                    if statevar in read: 
                        return True
                    else:
                        if statevar in written:
                            return False
                        else:
                            continue
                processed.append(node)
                for son in node.sons:
                    if son not in processed:
                        to_process.extend(node.sons)
                for fn in node.internal_calls:
                    if isinstance(fn, Function) and not isinstance(fn, SolidityFunction):
                        if fn.entry_point not in processed:
                            to_process.append(fn.entry_point)
            return False
    
    def is_r(self, statevar):
        if not (statevar in self.read and statevar not in self.written):
            return False 
        else:
            return True  
    
    def is_w(self, statevar):
        if not (statevar in self.written):
            return False 
        else:
            if statevar not in self.read:
                return True     
            else:
                all_nodes = self.fn.all_nodes()
                processed = list()
                cur_node = self.fn.entry_point
                to_process = list()
                to_process.append(cur_node)
                while len(to_process)>0:
                    node = to_process.pop()
                    if node in all_nodes and node not in processed:
                        read = node.state_variables_read
                        written = node.state_variables_written
                        if statevar in written and statevar not in read: 
                            return True
                        else:
                            if statevar in read:
                                return False
                            else:
                                continue
                    processed.append(node)
                    for son in node.sons:
                        if son not in processed:
                            to_process.extend(node.sons)
                    for fn in node.internal_calls:
                        if isinstance(fn, Function) and not isinstance(fn, SolidityFunction):
                            if fn.entry_point not in processed:
                                to_process.append(fn.entry_point)
                return False
    

def weak_depend(fn: FunctionContract, other_fn: FunctionContract):
        statevars = fn.contract.state_variables
        for statevar in statevars:
            if not (FunctionUtil(fn).is_r(statevar) or FunctionUtil(fn).is_w(statevar) or FunctionUtil(fn).is_rw(statevar)):
                continue 
            if  (
                    (FunctionUtil(fn).is_r(statevar) and FunctionUtil(other_fn).is_rw(statevar)) 
                or 
                    (FunctionUtil(fn).is_rw(statevar) and FunctionUtil(other_fn).is_rw(statevar)) 
                ):
                return True  

        return False

def strong_depend(fn: FunctionContract, other_fn: FunctionContract):
        statevars = fn.contract.state_variables
        for statevar in statevars:
            if not (FunctionUtil(fn).is_r(statevar) or FunctionUtil(fn).is_w(statevar) or FunctionUtil(fn).is_rw(statevar)):
                continue 
            if (FunctionUtil(fn).is_r(statevar) or FunctionUtil(fn).is_rw(statevar)) and FunctionUtil(other_fn).is_w(statevar):
                return True  
        return False

def build_dependency_tree(contract: Contract):
    weak_dependency_tree = dict() 
    strong_dependency_tree = dict()
    fns = [ fn for fn in contract.functions if fn.view == False and fn.pure == False and fn.is_constructor == False ]
    for pair in itertools.combinations(range(len(fns)), 2):
        fn_left, fn_right = fns[pair[0]], fns[pair[1]]
        # print(fn_left, fn_right, strong_depend(fn_left, fn_right), strong_depend(fn_right, fn_left), weak_depend(fn_left, fn_right), weak_depend(fn_right, fn_left))
        if strong_depend(fn_left, fn_right):
            if fn_left.canonical_name not in strong_dependency_tree:
                strong_dependency_tree[fn_left.canonical_name] = []
            strong_dependency_tree[fn_left.canonical_name].append(fn_right)
        elif weak_depend(fn_left, fn_right):
            if fn_left.canonical_name not in weak_dependency_tree:
                weak_dependency_tree[fn_left.canonical_name] = []
            weak_dependency_tree[fn_left.canonical_name].append(fn_right)
        elif strong_depend(fn_right, fn_left):
            if fn_right.canonical_name not in strong_dependency_tree:
                strong_dependency_tree[fn_right.canonical_name] = []
            strong_dependency_tree[fn_right.canonical_name].append(fn_left)
        elif weak_depend(fn_right, fn_left):
            if fn_right.canonical_name not in weak_dependency_tree:
                weak_dependency_tree[fn_right.canonical_name] = [] 
            weak_dependency_tree[fn_right.canonical_name].append(fn_left)

    return  weak_dependency_tree, strong_dependency_tree

ERC20_token_flow_fns = {
    "transfer", 
    "transferFrom",
}
ERC223_token_flow_fns = {
    "transfer"
}
ERC721_token_flow_fns = {
    "safeTransferFrom",
    "transferFrom"
}
ERC777_token_flow_fns = {
    "send",
    "operatorSend",
    "burn",
    "operatorBurn"
}
ERC1155_token_flow_fns = {
     "safeTransferFrom",
     "safeBatchTransferFrom",
}
ERC1363_token_flow_fns = {
    "transferAndCall",
    "transferFromAndCall"
}.union(ERC20_token_flow_fns)

ERC4524_token_flow_fns = {
   "safeTransfer",
   "safeTransferFrom"
}.union(ERC20_token_flow_fns) 

ERC4626_token_flow_fns = {
    "deposit",
    "previewMint",
    "mint", 
    "maxWithdraw",
    "previewWithdraw",
    "withdraw",
    "maxRedeem",
    "previewRedeem",
    "redeem"
}.union(ERC20_token_flow_fns)

ERCS = ERC20_token_flow_fns.union(
    ERC223_token_flow_fns).union(
        ERC223_token_flow_fns).union(ERC721_token_flow_fns).union(
            ERC777_token_flow_fns).union(ERC1155_token_flow_fns).union(
                ERC1363_token_flow_fns).union(
                    ERC4524_token_flow_fns).union(
                        ERC4626_token_flow_fns)

def build_dependency_tree_token_flow_or_money_flow(contract:Contract):
    weak_dependency_tree, strong_dependency_tree =  build_dependency_tree(contract)
    # print(weak_dependency_tree)
    # print(strong_dependency_tree)
    fns = [ fn for fn in contract.functions if fn.view == False and fn.pure == False \
        and (fn.can_send_eth() or fn.name in ERCS) ]
    money_flow_weak_dependency_tree =  dict()
    money_flow_strong_dependency_tree = dict() 
    for fn in fns:
        cur = fn
        process_list = [cur]
        processed = []
        while len(process_list) > 0:
            cur = process_list.pop()
            if cur not in processed and cur.canonical_name in weak_dependency_tree:
                processed.append(cur)
                money_flow_weak_dependency_tree[cur.canonical_name] = weak_dependency_tree[cur.canonical_name]
                process_list.extend(money_flow_weak_dependency_tree[cur.canonical_name])
        
        cur = fn
        process_list = [cur]
        processed = []
        while len(process_list) > 0:
            cur = process_list.pop()
            if cur not in processed and cur.canonical_name in strong_dependency_tree:
                processed.append(cur)
                money_flow_strong_dependency_tree[cur.canonical_name] = strong_dependency_tree[cur.canonical_name]
                process_list.extend(money_flow_strong_dependency_tree[cur.canonical_name])
    
    return money_flow_weak_dependency_tree, money_flow_strong_dependency_tree
            
               