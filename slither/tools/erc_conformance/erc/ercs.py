import logging
from collections import defaultdict

from slither.core.solidity_types import MappingType
from slither.slithir.operations import EventCall
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
            ret["missing_function"].append({
                "description": txt,
                "contract": contract.name,
                "function": sig,
                "required": required
            })
            return

        types = [str(x) for x in export_nested_types_from_variable(state_variable_as_function)]

        if types != parameters:
            txt = f'[ ] {sig} is missing {"" if required else "(optional)"}'
            logger.info(txt)
            ret["missing_function"].append({
                "description": txt,
                "contract": contract.name,
                "function": sig,
                "required": required
            })
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
            ret["incorrect_return_type"].append({
                "description": txt,
                "contract": contract.name,
                "function": sig,
                "expected_return_type": return_type,
                "actual_return_type": function_return_type
            })
            logger.info(txt)
    elif not return_type:
        txt = f'\t[✓] {sig} -> () (correct return type)'
        logger.info(txt)
    else:
        txt = f'\t[ ] {sig} -> () should return {return_type}'
        ret["incorrect_return_type"].append({
            "description": txt,
            "contract": contract.name,
            "function": sig,
            "expected_return_type": return_type,
            "actual_return_type": ""
        })
        logger.info(txt)

    if view:
        if function_view:
            txt = f'\t[✓] {sig} is view'
            logger.info(txt)
        else:
            txt = f'\t[ ] {sig} should be view'
            ret["should_be_view"].append({
                "description": txt,
                "contract": contract.name,
                "function": sig
            })
            logger.info(txt)

    if events:
        for event in events:
            event_sig = f'{event.name}({",".join(event.parameters)})'

            if not function:
                txt = f'\t[ ] Must emit be view {event_sig}'
                ret["missing_event_emmited"].append({
                    "description": txt,
                    "contract": contract.name,
                    "function": sig,
                    "missing_event": event_sig
                })
                logger.info(txt)
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
                    ret["missing_event_emmited"].append({
                        "description": txt,
                        "contract": contract.name,
                        "function": sig,
                        "missing_event": event_sig
                    })
                    logger.info(txt)




def _check_events(erc_event, contract, ret):
    name = erc_event.name
    parameters = erc_event.parameters
    indexes = erc_event.indexes

    sig = f'{name}({",".join(parameters)})'
    event = contract.get_event_from_signature(sig)

    if not event:
        txt = f'[ ] {sig} is missing'
        logger.info(txt)
        ret["missing_event"].append({
            "description": txt,
            "contract": contract.name,
            "event": sig
        })
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
                ret["missing_event_index"].append({
                    "description": txt,
                    "contract": contract.name,
                    "event": sig,
                    "missing_index": i
                })



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
