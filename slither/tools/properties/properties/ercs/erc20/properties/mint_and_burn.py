from slither.tools.properties.properties.properties import (
    Property,
    PropertyType,
    PropertyReturn,
    PropertyCaller,
)

ERC20_NotMintableNotBurnable = [
    Property(
        name="crytic_supply_constant_ERC20PropertiesNotMintableNotBurnable()",
        description="The total supply does not change.",
        content="""
\t\treturn initialTotalSupply == this.totalSupply();""",
        type=PropertyType.MEDIUM_SEVERITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),
]
