from slither.detectors.abstract_detector import (
    AbstractDetector,
    DETECTOR_INFO,
)
from slither.utils.output import Output
from slither.slithir.operations import Member, Binary, Assignment


class PythUnchecked(AbstractDetector):
    """
    Documentation: This detector finds deprecated Pyth function calls
    """

    # To be overridden in the derived class
    PYTH_FUNCTIONS = []
    PYTH_FIELD = ""

    def _detect(self) -> list[Output]:
        results: list[Output] = []

        for contract in self.compilation_unit.contracts_derived:
            for target_contract, ir in contract.all_high_level_calls:
                if target_contract.name == "IPyth" and ir.function_name in self.PYTH_FUNCTIONS:
                    # We know for sure the last IR in the node is an Assignment operation of the TMP variable. Example:
                    # 	Expression: price = pyth.getEmaPriceNoOlderThan(id,age)
                    #   IRs:
                    #      TMP_0(PythStructs.Price) = HIGH_LEVEL_CALL, dest:pyth(IPyth), function:getEmaPriceNoOlderThan, arguments:['id', 'age']
                    #      price(PythStructs.Price) := TMP_0(PythStructs.Price)
                    assert isinstance(ir.node.irs[len(ir.node.irs) - 1], Assignment)
                    return_variable = ir.node.irs[len(ir.node.irs) - 1].lvalue
                    checked = False

                    possible_unchecked_variable_ir = None
                    nodes = ir.node.sons
                    visited = set()
                    while nodes:
                        if checked:
                            break
                        next_node = nodes[0]
                        nodes = nodes[1:]

                        for node_ir in next_node.all_slithir_operations():
                            # We are accessing the unchecked_var field of the returned Price struct
                            if (
                                isinstance(node_ir, Member)
                                and node_ir.variable_left == return_variable
                                and node_ir.variable_right.name == self.PYTH_FIELD
                            ):
                                possible_unchecked_variable_ir = node_ir.lvalue
                            # We assume that if unchecked_var happens to be inside a binary operation is checked
                            if (
                                isinstance(node_ir, Binary)
                                and possible_unchecked_variable_ir is not None
                                and possible_unchecked_variable_ir in node_ir.read
                            ):
                                checked = True
                                break

                        if next_node not in visited:
                            visited.add(next_node)
                            for son in next_node.sons:
                                if son not in visited:
                                    nodes.append(son)

                    if not checked:
                        info: DETECTOR_INFO = [
                            f"Pyth price {self.PYTH_FIELD} field is not checked in ",
                            ir.node.function,
                            "\n\t- ",
                            ir.node,
                            "\n",
                        ]
                        res = self.generate_result(info)
                        results.append(res)

        return results
