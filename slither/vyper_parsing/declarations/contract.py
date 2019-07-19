import logging

from slither.core.declarations.contract import Contract
from .function import FunctionVyper
logger = logging.getLogger("ContractSolcParsing")

class ContractVyper(Contract):

    COUNTER = 0

    def __init__(self, slither, data_loaded):
        super(ContractVyper, self).__init__()

        self._id = ContractVyper.COUNTER
        ContractVyper.COUNTER += 1

        self._slither = slither

        all_public = False
        if 'ast_type' in data_loaded and data_loaded['ast_type'] == 'ClassDef':
            self._name = data_loaded['name']
            ast = data_loaded['body']
            all_public = True
        else:
            self._name = data_loaded['contract_name'][:-len('.vy')]
            ast = data_loaded['ast']

        assignement = [ass for ass in ast if ass['ast_type'] == 'AnnAssign']
        functions = [FunctionVyper(f, self) for f in ast if f['ast_type'] == 'FunctionDef']

        for f in functions:
            f.set_offset(None, slither)

            if all_public:
                f.set_visibility('public')

        self._functions = {f.name: f for f in functions}



    # endregion
    ###################################################################################
    ###################################################################################
    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __hash__(self):
        return self._id

    # endregion
