from slither.slither import Slither

slither = Slither("find.sol")
find = slither.get_contract_from_name("Find")[0]

assert find

# Get the variable
my_variable = find.get_state_variable_from_name("my_variable")
assert my_variable


function_using_a_as_condition = [
    f
    for f in find.functions
    if f.is_reading_in_conditional_node(my_variable)
    or f.is_reading_in_require_or_assert(my_variable)
]

# Print the result
print(f'The function using "a" in condition are {[f.name for f in function_using_a_as_condition]}')
