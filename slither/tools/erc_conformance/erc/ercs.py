import logging

from slither.slithir.operations import EventCall
from slither.utils import output
from slither.utils.type import (
    export_nested_types_from_variable,
    export_return_type_from_variable,
)

logger = logging.getLogger("Slither-conformance")


# pylint: disable=too-many-locals,too-many-branches,too-many-statements
def _check_signature(erc_function, contract, ret):
    name = erc_function.name
    parameters = erc_function.parameters
    return_type = erc_function.return_type
    view = erc_function.view
    required = erc_function.required
    events = erc_function.events

    sig = f'{name}({",".join(parameters)})'
    function = contract.get_function_from_signature(sig)

    if not function:
        # The check on state variable is needed until we have a better API to handle state variable getters
        state_variable_as_function = contract.get_state_variable_from_name(name)

        if (
            not state_variable_as_function
            or not state_variable_as_function.visibility in ["public", "external",]
        ):
            txt = f'[ ] {sig} is missing {"" if required else "(optional)"}'
            logger.info(txt)
            missing_func = output.Output(
                txt, additional_fields={"function": sig, "required": required}
            )
            missing_func.add(contract)
            ret["missing_function"].append(missing_func.data)
            return

        types = [
            str(x)
            for x in export_nested_types_from_variable(state_variable_as_function)
        ]

        if types != parameters:
            txt = f'[ ] {sig} is missing {"" if required else "(optional)"}'
            logger.info(txt)
            missing_func = output.Output(
                txt, additional_fields={"function": sig, "required": required}
            )
            missing_func.add(contract)
            ret["missing_function"].append(missing_func.data)
            return

        function_return_type = [
            export_return_type_from_variable(state_variable_as_function)
        ]
        function = state_variable_as_function

        function_view = True
    else:
        function_return_type = function.return_type  # pylint: disable=no-member
        function_view = function.view  # pylint: disable=no-member

    txt = f"[✓] {sig} is present"
    logger.info(txt)

    if function_return_type:
        function_return_type = ",".join([str(x) for x in function_return_type])
        if function_return_type == return_type:
            txt = f"\t[✓] {sig} -> () (correct return value)"
            logger.info(txt)
        else:
            txt = f"\t[ ] {sig} -> () should return {return_type}"
            logger.info(txt)

            incorrect_return = output.Output(
                txt,
                additional_fields={
                    "expected_return_type": return_type,
                    "actual_return_type": function_return_type,
                },
            )
            incorrect_return.add(function)
            ret["incorrect_return_type"].append(incorrect_return.data)

    elif not return_type:
        txt = f"\t[✓] {sig} -> () (correct return type)"
        logger.info(txt)
    else:
        txt = f"\t[ ] {sig} -> () should return {return_type}"
        logger.info(txt)

        incorrect_return = output.Output(
            txt,
            additional_fields={
                "expected_return_type": return_type,
                "actual_return_type": function_return_type,
            },
        )
        incorrect_return.add(function)
        ret["incorrect_return_type"].append(incorrect_return.data)

    if view:
        if function_view:
            txt = f"\t[✓] {sig} is view"
            logger.info(txt)
        else:
            txt = f"\t[ ] {sig} should be view"
            logger.info(txt)

            should_be_view = output.Output(txt)
            should_be_view.add(function)
            ret["should_be_view"].append(should_be_view.data)

    if events:  # pylint: disable=too-many-nested-blocks
        for event in events:
            event_sig = f'{event.name}({",".join(event.parameters)})'

            if not function:
                txt = f"\t[ ] Must emit be view {event_sig}"
                logger.info(txt)

                missing_event_emmited = output.Output(
                    txt, additional_fields={"missing_event": event_sig}
                )
                missing_event_emmited.add(function)
                ret["missing_event_emmited"].append(missing_event_emmited.data)

            else:
                event_found = False
                for ir in function.all_slithir_operations():
                    if isinstance(ir, EventCall):
                        if ir.name == event.name:
                            if event.parameters == [str(a.type) for a in ir.arguments]:
                                event_found = True
                                break
                if event_found:
                    txt = f"\t[✓] {event_sig} is emitted"
                    logger.info(txt)
                else:
                    txt = f"\t[ ] Must emit be view {event_sig}"
                    logger.info(txt)

                    missing_event_emmited = output.Output(
                        txt, additional_fields={"missing_event": event_sig}
                    )
                    missing_event_emmited.add(function)
                    ret["missing_event_emmited"].append(missing_event_emmited.data)


def _check_events(erc_event, contract, ret):
    name = erc_event.name
    parameters = erc_event.parameters
    indexes = erc_event.indexes

    sig = f'{name}({",".join(parameters)})'
    event = contract.get_event_from_signature(sig)

    if not event:
        txt = f"[ ] {sig} is missing"
        logger.info(txt)

        missing_event = output.Output(txt, additional_fields={"event": sig})
        missing_event.add(contract)
        ret["missing_event"].append(missing_event.data)
        return

    txt = f"[✓] {sig} is present"
    logger.info(txt)

    for i, index in enumerate(indexes):
        if index:
            if event.elems[i].indexed:
                txt = f"\t[✓] parameter {i} is indexed"
                logger.info(txt)
            else:
                txt = f"\t[ ] parameter {i} should be indexed"
                logger.info(txt)

                missing_event_index = output.Output(
                    txt, additional_fields={"missing_index": i}
                )
                missing_event_index.add_event(event)
                ret["missing_event_index"].append(missing_event_index.data)


def generic_erc_checks(contract, erc_functions, erc_events, ret, explored=None):

    if explored is None:
        explored = set()

    explored.add(contract)

    logger.info(f"# Check {contract.name}\n")

    logger.info("## Check functions")
    for erc_function in erc_functions:
        _check_signature(erc_function, contract, ret)
    logger.info("\n## Check events")
    for erc_event in erc_events:
        _check_events(erc_event, contract, ret)

    logger.info("\n")

    for derived_contract in contract.derived_contracts:
        generic_erc_checks(derived_contract, erc_functions, erc_events, ret, explored)
