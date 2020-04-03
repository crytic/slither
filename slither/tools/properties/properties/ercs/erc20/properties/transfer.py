from slither.tools.properties.properties.properties import Property, PropertyType, PropertyReturn, PropertyCaller

ERC20_Transferable = [

    Property(name='crytic_zero_always_empty_ERC20Properties()',
             description='The address 0x0 should not receive tokens.',
             content='''
\t\treturn this.balanceOf(address(0x0)) == 0;''',
             type=PropertyType.CODE_QUALITY,
             return_type=PropertyReturn.SUCCESS,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ANY),

    Property(name='crytic_approve_overwrites()',
             description='Allowance can be changed.',
             content='''
\t\tbool approve_return; 
\t\tapprove_return = approve(crytic_user, 10);
\t\trequire(approve_return);
\t\tapprove_return = approve(crytic_user, 20);
\t\trequire(approve_return);
\t\treturn this.allowance(msg.sender, crytic_user) == 20;''',
             type=PropertyType.CODE_QUALITY,
             return_type=PropertyReturn.SUCCESS,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),

    Property(name='crytic_less_than_total_ERC20Properties()',
             description='Balance of one user must be less or equal to the total supply.',
             content='''
\t\treturn this.balanceOf(msg.sender) <= totalSupply();''',
             type=PropertyType.MEDIUM_SEVERITY,
             return_type=PropertyReturn.SUCCESS,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),

    Property(name='crytic_totalSupply_consistant_ERC20Properties()',
             description='Balance of the crytic users must be less or equal to the total supply.',
             content='''
\t\treturn this.balanceOf(crytic_owner) + this.balanceOf(crytic_user) + this.balanceOf(crytic_attacker) <= totalSupply();''',
             type=PropertyType.MEDIUM_SEVERITY,
             return_type=PropertyReturn.SUCCESS,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ANY),

    Property(name='crytic_revert_transfer_to_zero_ERC20PropertiesTransferable()',
             description='No one should be able to send tokens to the address 0x0 (transfer).',
             content='''
\t\tif (this.balanceOf(msg.sender) == 0){
\t\t\trevert();
\t\t}
\t\treturn transfer(address(0x0), this.balanceOf(msg.sender));''',
             type=PropertyType.CODE_QUALITY,
             return_type=PropertyReturn.FAIL_OR_THROW,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),

    Property(name='crytic_revert_transferFrom_to_zero_ERC20PropertiesTransferable()',
             description='No one should be able to send tokens to the address 0x0 (transferFrom).',
             content='''
\t\tuint balance = this.balanceOf(msg.sender);
\t\tif (balance == 0){
\t\t\trevert();
\t\t}
\t\tapprove(msg.sender, balance);
\t\treturn transferFrom(msg.sender, address(0x0), this.balanceOf(msg.sender));''',
             type=PropertyType.CODE_QUALITY,
             return_type=PropertyReturn.FAIL_OR_THROW,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),

    Property(name='crytic_self_transferFrom_ERC20PropertiesTransferable()',
             description='Self transferFrom works.',
             content='''
\t\tuint balance = this.balanceOf(msg.sender);
\t\tbool approve_return = approve(msg.sender, balance);
\t\tbool transfer_return = transferFrom(msg.sender, msg.sender, balance);
\t\treturn (this.balanceOf(msg.sender) == balance) && approve_return && transfer_return;''',
             type=PropertyType.HIGH_SEVERITY,
             return_type=PropertyReturn.SUCCESS,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),

    Property(name='crytic_self_transferFrom_to_other_ERC20PropertiesTransferable()',
             description='transferFrom works.',
             content='''
\t\tuint balance = this.balanceOf(msg.sender);
\t\tbool approve_return = approve(msg.sender, balance);
\t\taddress other = crytic_user;
\t\tif (other == msg.sender) {
\t\t\tother = crytic_owner;
\t\t}
\t\tbool transfer_return = transferFrom(msg.sender, other, balance);
\t\treturn (this.balanceOf(msg.sender) == 0) && approve_return && transfer_return;''',
             type=PropertyType.HIGH_SEVERITY,
             return_type=PropertyReturn.SUCCESS,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),


    Property(name='crytic_self_transfer_ERC20PropertiesTransferable()',
             description='Self transfer works.',
             content='''
\t\tuint balance = this.balanceOf(msg.sender);
\t\tbool transfer_return = transfer(msg.sender, balance);
\t\treturn (this.balanceOf(msg.sender) == balance) && transfer_return;''',
             type=PropertyType.HIGH_SEVERITY,
             return_type=PropertyReturn.SUCCESS,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),

    Property(name='crytic_transfer_to_other_ERC20PropertiesTransferable()',
             description='transfer works.',
             content='''
\t\tuint balance = this.balanceOf(msg.sender);
\t\taddress other = crytic_user;
\t\tif (other == msg.sender) {
\t\t\tother = crytic_owner;
\t\t}
\t\tif (balance >= 1) {
\t\t\tbool transfer_other = transfer(other, 1);
\t\t\treturn (this.balanceOf(msg.sender) == balance-1) && (this.balanceOf(other) >= 1) && transfer_other;
\t\t}
\t\treturn true;''',
             type=PropertyType.HIGH_SEVERITY,
             return_type=PropertyReturn.SUCCESS,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),

    Property(name='crytic_revert_transfer_to_user_ERC20PropertiesTransferable()',
             description='Cannot transfer more than the balance.',
             content='''
\t\tuint balance = this.balanceOf(msg.sender);
\t\tif (balance == (2 ** 256 - 1))
\t\t\treturn true;
\t\tbool transfer_other = transfer(crytic_user, balance+1);
\t\treturn transfer_other;''',
             type=PropertyType.HIGH_SEVERITY,
             return_type=PropertyReturn.FAIL_OR_THROW,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),

]


ERC20_Pausable = [

    Property(name='crytic_revert_transfer_ERC20AlwaysTruePropertiesNotTransferable()',
             description='Cannot transfer.',
             content='''
\t\treturn transfer(crytic_user, this.balanceOf(msg.sender));''',
             type=PropertyType.MEDIUM_SEVERITY,
             return_type=PropertyReturn.FAIL_OR_THROW,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),

    Property(name='crytic_revert_transferFrom_ERC20AlwaysTruePropertiesNotTransferable()',
             description='Cannot execute transferFrom.',
             content='''
\t\tapprove(msg.sender, this.balanceOf(msg.sender));
\t\ttransferFrom(msg.sender, msg.sender, this.balanceOf(msg.sender));''',
             type=PropertyType.MEDIUM_SEVERITY,
             return_type=PropertyReturn.FAIL_OR_THROW,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),

    Property(name='crytic_constantBalance()',
             description='Cannot change the balance.',
             content='''
\t\treturn this.balanceOf(crytic_user) == initialBalance_user && this.balanceOf(crytic_attacker) == initialBalance_attacker;''',
             type=PropertyType.MEDIUM_SEVERITY,
             return_type=PropertyReturn.SUCCESS,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),

    Property(name='crytic_constantAllowance()',
             description='Cannot change the allowance.',
             content='''
\t\treturn (this.allowance(crytic_user, crytic_attacker) == initialAllowance_user_attacker) &&
\t\t\t(this.allowance(crytic_attacker, crytic_attacker) == initialAllowance_attacker_attacker);''',
             type=PropertyType.MEDIUM_SEVERITY,
             return_type=PropertyReturn.SUCCESS,
             is_unit_test=True,
             is_property_test=True,
             caller=PropertyCaller.ALL),

]


