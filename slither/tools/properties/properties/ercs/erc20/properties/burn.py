from slither.tools.properties.properties.properties import (
    Property,
    PropertyType,
    PropertyReturn,
    PropertyCaller,
)

ERC20_NotBurnable = [
    Property(
        name="crytic_supply_constant_ERC20PropertiesNotBurnable()",
        description="The total supply does not decrease.",
        content="""
\t\treturn initialTotalSupply == this.totalSupply();""",
        type=PropertyType.MEDIUM_SEVERITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),
]


# Require burn(address) returns()
ERC20_Burnable = [
    Property(
        name="crytic_supply_constant_ERC20PropertiesNotBurnable()",
        description="Cannot burn more than available balance",
        content="""
\t\tuint balance = balanceOf(msg.sender);
\t\tburn(balance + 1);
\t\treturn false;""",
        type=PropertyType.MEDIUM_SEVERITY,
        return_type=PropertyReturn.THROW,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ALL,
    )
]
