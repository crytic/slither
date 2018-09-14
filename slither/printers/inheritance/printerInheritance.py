"""
    Module printing the inheritance graph

    The inheritance graph shows the relation between the contracts
    and their functions/modifiers/public variables.
    The output is a dot file named filename.dot
"""

from slither.core.declarations.contract import Contract
from slither.detectors.shadowing.shadowingFunctionsDetection import ShadowingFunctionsDetection
from slither.printers.abstract_printer import AbstractPrinter


class PrinterInheritance(AbstractPrinter):
    ARGUMENT = 'inheritance'
    HELP = 'the inheritance graph'

    def __init__(self, slither, logger):
        super(PrinterInheritance, self).__init__(slither, logger)

        inheritance = [x.inheritance for x in slither.contracts]
        self.inheritance = set([item for sublist in inheritance for item in sublist])

        shadow = ShadowingFunctionsDetection(slither, None)
        ret = shadow.detect()
        functions_shadowed = {}
        for s in ret:
            if s['contractShadower'] not in functions_shadowed:
                functions_shadowed[s['contractShadower']] = []
            functions_shadowed[s['contractShadower']] += s['funcs']
        self.functions_shadowed = functions_shadowed

    def _get_pattern_func(self, func, contract):
        # Html pattern, each line is a row in a table
        func_name = func.full_name
        pattern = '<TR><TD align="left">    %s</TD></TR>'
        pattern_shadow = '<TR><TD align="left"><font color="#FFA500">    %s</font></TD></TR>'
        if contract.name in self.functions_shadowed:
            if func_name in self.functions_shadowed[contract.name]:
                return pattern_shadow % func_name
        return pattern % func_name

    def _get_pattern_var(self, var, contract):
        # Html pattern, each line is a row in a table
        var_name = var.name
        pattern = '<TR><TD align="left">    %s</TD></TR>'
        pattern_contract = '<TR><TD align="left">    %s<font color="blue" POINT-SIZE="10"> (%s)</font></TD></TR>'
        # pattern_arrow  = '<TR><TD align="left" PORT="%s"><font color="blue">    %s</font></TD></TR>'
        if isinstance(var.type, Contract):
            return pattern_contract % (var_name, str(var.type))
            # return pattern_arrow%(self._get_port_id(var, contract), var_name)
        return pattern % var_name

    def _get_port_id(self, var, contract):
        return "%s%s" % (var.name, contract.name)

    def _summary(self, contract):
        """
            Build summary using HTML
        """
        ret = ''
        # Add arrows
        for i in contract.inheritance:
            ret += '%s -> %s;\n' % (contract.name, i)

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
                            v.visibility in visibilities]
        public_variables = ''.join(public_variables)

        private_variables = [self._get_pattern_var(v, contract) for v in contract.variables if
                             not v.visibility in visibilities]
        private_variables = ''.join(private_variables)

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
        ret += '</TABLE> >];\n'

        return ret

    def output(self, filename):
        """
            Output the graph in filename
            Args:
                filename(string)
        """
        if not filename.endswith('.dot'):
            filename += ".dot"
        info = 'Inheritance Graph: ' + filename
        self.info(info)
        with open(filename, 'w') as f:
            f.write('digraph{\n')
            for c in self.contracts:
                f.write(self._summary(c))
            f.write('}')
