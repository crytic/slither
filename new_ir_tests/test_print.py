from slither import Slither
from slither.analyses.data_dependency.data_dependency import is_dependent, Access, KEY_GRAPH, Graph, _tmp_to_str
from slither.slithir.variables import Constant

sl = Slither('simple_nested_with_mapping.sol')

contract_C = sl.get_contract_from_name('C')
assert contract_C

st1 = contract_C.get_state_variable_from_name('st1')
st2 = contract_C.get_state_variable_from_name('st2')
ret = contract_C.get_state_variable_from_name('ret')
ret2 = contract_C.get_state_variable_from_name('ret2')
n = contract_C.get_state_variable_from_name('n')
map = contract_C.get_state_variable_from_name('map')
map2 = contract_C.get_state_variable_from_name('map2')
sts = contract_C.get_state_variable_from_name('sts')
nestednested = contract_C.get_state_variable_from_name('nestednested')

g = contract_C.get_function_from_signature('g(uint256)')
f = contract_C.get_function_from_signature('f(uint256)')
t = contract_C.get_function_from_signature('t(uint256)')
i = contract_C.get_function_from_signature('i(uint256)')
j = contract_C.get_function_from_signature('j(uint256)')
k = contract_C.get_function_from_signature('k(uint256,uint256)')
f1 = contract_C.get_function_from_signature('f1(uint256)')

graph: Graph= k.context[KEY_GRAPH]

nestednested_mn_s_one = Access(nestednested, [Constant('mn'), Constant('s'), Constant('one')])
nestednested_mn_s_two = Access(nestednested, [Constant('mn'), Constant('s'), Constant('two')])
print('Print deps')
deps = graph.get_dependencies(nestednested_mn_s_two.to_tuple(), False)
print('####')
for dep in deps:
    print(_tmp_to_str(dep))