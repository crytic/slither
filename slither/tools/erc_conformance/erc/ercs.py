import logging

from slither.slithir.operations import EventCall
from slither.utils import json_utils
from slither.utils.type import export_nested_types_from_variable, export_return_type_from_variable

logger = logging.getLogger("Slither-conformance")


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

        if not state_variable_as_function or not state_variable_as_function.visibility in ['public', 'external']:
            txt = f'[ ] {sig} is missing {"" if required else "(optional)"}'
            logger.info(txt)
            missing_func = json_utils.generate_json_result(txt, additional_fields={
                "function": sig,
                "required": required
            })
            json_utils.add_contract_to_json(contract, missing_func)
            ret["missing_function"].append(missing_func)
            return

        types = [str(x) for x in export_nested_types_from_variable(state_variable_as_function)]

        if types != parameters:
            txt = f'[ ] {sig} is missing {"" if required else "(optional)"}'
            logger.info(txt)
            missing_func = json_utils.generate_json_result(txt, additional_fields={
                "function": sig,
                "required": required
            })
            json_utils.add_contract_to_json(contract, missing_func)
            ret["missing_function"].append(missing_func)
            return

        function_return_type = [export_return_type_from_variable(state_variable_as_function)]

        function_view = True
    else:
        function_return_type = function.return_type
        function_view = function.view

    txt = f'[✓] {sig} is present'
    logger.info(txt)

    if function_return_type:
        function_return_type = ','.join([str(x) for x in function_return_type])
        if function_return_type == return_type:
            txt = f'\t[✓] {sig} -> () (correct return value)'
            logger.info(txt)
        else:
            txt = f'\t[ ] {sig} -> () should return {return_type}'
            logger.info(txt)

            incorrect_return = json_utils.generate_json_result(txt, additional_fields={
                "expected_return_type": return_type,
                "actual_return_type": function_return_type
            })
            json_utils.add_function_to_json(function, incorrect_return)
            ret["incorrect_return_type"].append(incorrect_return)

    elif not return_type:
        txt = f'\t[✓] {sig} -> () (correct return type)'
        logger.info(txt)
    else:
        txt = f'\t[ ] {sig} -> () should return {return_type}'
        logger.info(txt)

        incorrect_return = json_utils.generate_json_result(txt, additional_fields={
            "expected_return_type": return_type,
            "actual_return_type": function_return_type
        })
        json_utils.add_function_to_json(function, incorrect_return)
        ret["incorrect_return_type"].append(incorrect_return)

    if view:
        if function_view:
            txt = f'\t[✓] {sig} is view'
            logger.info(txt)
        else:
            txt = f'\t[ ] {sig} should be view'
            logger.info(txt)

            should_be_view = json_utils.generate_json_result(txt)
            json_utils.add_function_to_json(function, should_be_view)
            ret["should_be_view"].append(should_be_view)

    if events:
        for event in events:
            event_sig = f'{event.name}({",".join(event.parameters)})'

            if not function:
                txt = f'\t[ ] Must emit be view {event_sig}'
                logger.info(txt)

                missing_event_emmited = json_utils.generate_json_result(txt, additional_fields={
                    "missing_event": event_sig
                })
                json_utils.add_function_to_json(function, missing_event_emmited)
                ret["missing_event_emmited"].append(missing_event_emmited)

            else:
                event_found = False
                for ir in function.all_slithir_operations():
                    if isinstance(ir, EventCall):
                        if ir.name == event.name:
                            if event.parameters == [str(a.type) for a in ir.arguments]:
                                event_found = True
                                break
                if event_found:
                    txt = f'\t[✓] {event_sig} is emitted'
                    logger.info(txt)
                else:
                    txt = f'\t[ ] Must emit be view {event_sig}'
                    logger.info(txt)

                    missing_event_emmited = json_utils.generate_json_result(txt, additional_fields={
                        "missing_event": event_sig
                    })
                    json_utils.add_function_to_json(function, missing_event_emmited)
                    ret["missing_event_emmited"].append(missing_event_emmited)


def _check_events(erc_event, contract, ret):
    name = erc_event.name
    parameters = erc_event.parameters
    indexes = erc_event.indexes

    sig = f'{name}({",".join(parameters)})'
    event = contract.get_event_from_signature(sig)

    if not event:
        txt = f'[ ] {sig} is missing'
        logger.info(txt)

        missing_event = json_utils.generate_json_result(txt, additional_fields={
            "event": sig
        })
        json_utils.add_contract_to_json(contract, missing_event)
        ret["missing_event"].append(missing_event)

        return

    txt = f'[✓] {sig} is present'
    logger.info(txt)

    for i, index in enumerate(indexes):
        if index:
            if event.elems[i].indexed:
                txt = f'\t[✓] parameter {i} is indexed'
                logger.info(txt)
            else:
                txt = f'\t[ ] parameter {i} should be indexed'
                logger.info(txt)

                missing_event_index = json_utils.generate_json_result(txt, additional_fields={
                    "missing_index": i
                })
                json_utils.add_event_to_json(event, missing_event_index)
                ret["missing_event_index"].append(missing_event_index)


def generic_erc_checks(contract, erc_functions, erc_events, ret, explored=None):

    if explored is None:
        explored = set()

    explored.add(contract)

    logger.info(f'# Check {contract.name}\n')

    logger.info(f'## Check functions')
    for erc_function in erc_functions:
        _check_signature(erc_function, contract, ret)
    logger.info(f'\n## Check events')
    for erc_event in erc_events:
        _check_events(erc_event, contract, ret)

    logger.info('\n')

    for derived_contract in contract.derived_contracts:
        generic_erc_checks(derived_contract, erc_functions, erc_events, ret, explored)
