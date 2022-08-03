from slither.tools.properties.properties.properties import (
    PropertyType,
    PropertyReturn,
    Property,
    PropertyCaller,
)

ERC20_NotMintable = [
    Property(
        name="crytic_supply_constant_ERC20PropertiesNotMintable()",
        description="The total supply does not increase.",
        content="""
\t\treturn initialTotalSupply >= this.totalSupply();""",
        type=PropertyType.MEDIUM_SEVERITY,
        return_type=PropertyReturn.SUCCESS,
        is_unit_test=True,
        is_property_test=True,
        caller=PropertyCaller.ANY,
    ),
]
