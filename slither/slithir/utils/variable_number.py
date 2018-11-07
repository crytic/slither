from slither.slithir.variables import (Constant, ReferenceVariable,
                                       TemporaryVariable, TupleVariable)
from slither.slithir.operations import OperationWithLValue

def transform_slithir_vars_to_ssa(function):
    """
        Transform slithIR vars to SSA
    """
    variables = []
    for node in function.nodes:
        for ir in node.irs:
            if isinstance(ir, OperationWithLValue) and not ir.lvalue in variables:
                variables += [ir.lvalue]

    tmp_variables = [v for v in variables if isinstance(v, TemporaryVariable)]
    for idx in range(len(tmp_variables)):
        tmp_variables[idx].index = idx
    ref_variables = [v for v in variables if isinstance(v, ReferenceVariable)]
    for idx in range(len(ref_variables)):
        ref_variables[idx].index = idx
    tuple_variables = [v for v in variables if isinstance(v, TupleVariable)]
    for idx in range(len(tuple_variables)):
        tuple_variables[idx].index = idx
