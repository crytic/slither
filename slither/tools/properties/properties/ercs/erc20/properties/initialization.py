from slither.tools.properties.properties.properties import (
    Property,
    PropertyType,
    PropertyReturn,
    PropertyCaller,
)

ERC20_CONFIG = [
    Property(
        name="init_total_supply()",
        description="The total supply is correctly initialized.",
        content="""
\t\treturn this.totalSupply() >= 0 && this.totalSupply() == initialTotalSupply;""",
        type=PropertyType.CODE_QUALITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=False,
        caller=PropertyCaller.ANY,
    ),
    Property(
        name="init_owner_balance()",
        description="Owner's balance is correctly initialized.",
        content="""
\t\treturn initialBalance_owner == this.balanceOf(crytic_owner);""",
        type=PropertyType.CODE_QUALITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=False,
        caller=PropertyCaller.ANY,
    ),
    Property(
        name="init_user_balance()",
        description="User's balance is correctly initialized.",
        content="""
\t\treturn initialBalance_user == this.balanceOf(crytic_user);""",
        type=PropertyType.CODE_QUALITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=False,
        caller=PropertyCaller.ANY,
    ),
    Property(
        name="init_attacker_balance()",
        description="Attacker's balance is correctly initialized.",
        content="""
\t\treturn initialBalance_attacker == this.balanceOf(crytic_attacker);""",
        type=PropertyType.CODE_QUALITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=False,
        caller=PropertyCaller.ANY,
    ),
    Property(
        name="init_caller_balance()",
        description="All the users have a positive balance.",
        content="""
\t\treturn this.balanceOf(msg.sender) >0 ;""",
        type=PropertyType.CODE_QUALITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=False,
        caller=PropertyCaller.ALL,
    ),
    # Note: there is a potential overflow on the addition, but we dont consider it
    Property(
        name="init_total_supply_is_balances()",
        description="The total supply is the user and owner balance.",
        content="""
\t\treturn this.balanceOf(crytic_owner) + this.balanceOf(crytic_user) + this.balanceOf(crytic_attacker) == this.totalSupply();""",
        type=PropertyType.CODE_QUALITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=False,
        caller=PropertyCaller.ANY,
    ),
]
