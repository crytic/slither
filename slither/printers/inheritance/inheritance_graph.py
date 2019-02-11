"""
    Module printing the inheritance graph

    The inheritance graph shows the relation between the contracts
    and their functions/modifiers/public variables.
    The output is a dot file named filename.dot
"""

from slither.core.declarations.contract import Contract
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.inheritance_analysis import (detect_c3_function_shadowing,
                                                detect_function_shadowing,
                                                detect_state_variable_shadowing)


class PrinterInheritanceGraph(AbstractPrinter):
    ARGUMENT = 'inheritance-graph'
    HELP = 'Export the inheritance graph of each contract to a dot file'

    WIKI = 'https://github.com/trailofbits/slither/wiki/Printer-documentation#inheritance-graph'

    def __init__(self, slither, logger):
        super(PrinterInheritanceGraph, self).__init__(slither, logger)

        inheritance = [x.inheritance for x in slither.contracts]
        self.inheritance = set([item for sublist in inheritance for item in sublist])

        # Create a lookup of direct shadowing instances.
        self.direct_overshadowing_functions = {}
        shadows = detect_function_shadowing(slither.contracts, True, False)
        for overshadowing_instance in shadows:
            overshadowing_function = overshadowing_instance[2]

            # Add overshadowing function entry.
            if overshadowing_function not in self.direct_overshadowing_functions:
                self.direct_overshadowing_functions[overshadowing_function] = set()
            self.direct_overshadowing_functions[overshadowing_function].add(overshadowing_instance)

        # Create a lookup of shadowing state variables.
        # Format: { colliding_variable : set([colliding_variables]) }
        self.overshadowing_state_variables = {}
        shadows = detect_state_variable_shadowing(slither.contracts)
        for overshadowing_instance in shadows:
            overshadowing_state_var = overshadowing_instance[1]
            overshadowed_state_var = overshadowing_instance[3]

            # Add overshadowing variable entry.
            if overshadowing_state_var not in self.overshadowing_state_variables:
                self.overshadowing_state_variables[overshadowing_state_var] = set()
            self.overshadowing_state_variables[overshadowing_state_var].add(overshadowed_state_var)

    def _get_pattern_func(self, func, contract):
        # Html pattern, each line is a row in a table
        func_name = func.full_name
        pattern = '<TR><TD align="left">    %s</TD></TR>'
        pattern_shadow = '<TR><TD align="left"><font color="#FFA500">    %s</font></TD></TR>'
        if func in self.direct_overshadowing_functions:
            return pattern_shadow % func_name
        return pattern % func_name

    def _get_pattern_var(self, var, contract):
        # Html pattern, each line is a row in a table
        var_name = var.name
        pattern = '<TR><TD align="left">    %s</TD></TR>'
        pattern_contract = '<TR><TD align="left">    %s<font color="blue" POINT-SIZE="10"> (%s)</font></TD></TR>'
        pattern_shadow = '<TR><TD align="left"><font color="red">    %s</font></TD></TR>'
        pattern_contract_shadow = '<TR><TD align="left"><font color="red">    %s</font><font color="blue" POINT-SIZE="10"> (%s)</font></TD></TR>'

        if isinstance(var.type, UserDefinedType) and isinstance(var.type.type, Contract):
            if var in self.overshadowing_state_variables:
                return pattern_contract_shadow % (var_name, var.type.type.name)
            else:
                return pattern_contract % (var_name, var.type.type.name)
        else:
            if var in self.overshadowing_state_variables:
                return pattern_shadow % var_name
            else:
                return pattern % var_name

    @staticmethod
    def _get_indirect_shadowing_information(contract):
        """
        Obtain a string that describes variable shadowing for the given variable. None if no shadowing exists.
        :param var: The variable to collect shadowing information for.
        :param contract: The contract in which this variable is being analyzed.
        :return: Returns a string describing variable shadowing for the given variable. None if no shadowing exists.
        """
        # If this variable is an overshadowing variable, we'll want to return information describing it.
        result = []
        indirect_shadows = detect_c3_function_shadowing(contract)
        if indirect_shadows:
            for collision_set in sorted(indirect_shadows, key=lambda x: x[0][1].name):
                winner = collision_set[-1][1].contract.name
                collision_steps = [colliding_function.contract.name for _, colliding_function in collision_set]
                collision_steps = ', '.join(collision_steps)
                result.append(f"'{collision_set[0][1].full_name}' collides in inherited contracts {collision_steps} where {winner} is chosen.")
        return '\n'.join(result)

    def _get_port_id(self, var, contract):
        return "%s%s" % (var.name, contract.name)

    def _summary(self, contract):
        """
            Build summary using HTML
        """
        ret = ''

        # Add arrows (number them if there is more than one path so we know order of declaration for inheritance).
        if len(contract.immediate_inheritance) == 1:
            ret += '%s -> %s;\n' % (contract.name, contract.immediate_inheritance[0])
        else:
            for i in range(0, len(contract.immediate_inheritance)):
                ret += '%s -> %s [ label="%s" ];\n' % (contract.name, contract.immediate_inheritance[i], i + 1)

        # Functions
        visibilities = ['public', 'external']
        public_functions = [self._get_pattern_func(f, contract) for f in contract.functions if
                            not f.is_constructor and f.contract == contract and f.visibility in visibilities]
        public_functions = ''.join(public_functions)
        private_functions = [self._get_pattern_func(f, contract) for f in contract.functions if
                             not f.is_constructor and f.contract == contract and f.visibility not in visibilities]
        private_functions = ''.join(private_functions)

        # Modifiers
        modifiers = [self._get_pattern_func(m, contract) for m in contract.modifiers if m.contract == contract]
        modifiers = ''.join(modifiers)

        # Public variables
        public_variables = [self._get_pattern_var(v, contract) for v in contract.variables if
                            v.contract == contract and v.visibility in visibilities]
        public_variables = ''.join(public_variables)

        private_variables = [self._get_pattern_var(v, contract) for v in contract.variables if
                             v.contract == contract and v.visibility not in visibilities]
        private_variables = ''.join(private_variables)

        # Obtain any indirect shadowing information for this node.
        indirect_shadowing_information = self._get_indirect_shadowing_information(contract)

        # Build the node label
        ret += '%s[shape="box"' % contract.name
        ret += 'label=< <TABLE border="0">'
        ret += '<TR><TD align="center"><B>%s</B></TD></TR>' % contract.name
        if public_functions:
            ret += '<TR><TD align="left"><I>Public Functions:</I></TD></TR>'
            ret += '%s' % public_functions
        if private_functions:
            ret += '<TR><TD align="left"><I>Private Functions:</I></TD></TR>'
            ret += '%s' % private_functions
        if modifiers:
            ret += '<TR><TD align="left"><I>Modifiers:</I></TD></TR>'
            ret += '%s' % modifiers
        if public_variables:
            ret += '<TR><TD align="left"><I>Public Variables:</I></TD></TR>'
            ret += '%s' % public_variables
        if private_variables:
            ret += '<TR><TD align="left"><I>Private Variables:</I></TD></TR>'
            ret += '%s' % private_variables

        if indirect_shadowing_information:
            ret += '<TR><TD><BR/></TD></TR><TR><TD align="left" border="1"><font color="#777777" point-size="10">%s</font></TD></TR>' % indirect_shadowing_information.replace('\n', '<BR/>')
        ret += '</TABLE> >];\n'

        return ret

    def output(self, filename):
        """
            Output the graph in filename
            Args:
                filename(string)
        """
        if filename == '':
            filename = 'contracts.dot'
        if not filename.endswith('.dot'):
            filename += ".dot"
        info = 'Inheritance Graph: ' + filename
        self.info(info)
        with open(filename, 'w', encoding='utf8') as f:
            f.write('digraph "" {\n')
            for c in self.contracts:
                f.write(self._summary(c))
            f.write('}')
