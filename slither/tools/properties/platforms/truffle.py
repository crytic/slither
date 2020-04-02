import logging
import re
from pathlib import Path
from typing import List

from slither.tools.properties.addresses.address import Addresses
from slither.tools.properties.properties.properties import PropertyReturn, Property, PropertyCaller
from slither.tools.properties.utils import write_file

PATTERN_TRUFFLE_MIGRATION = re.compile('^[0-9]*_')
logger = logging.getLogger("Slither")


def _extract_caller(p: PropertyCaller):
    if p == PropertyCaller.OWNER:
        return ['owner']
    if p == PropertyCaller.SENDER:
        return ['user']
    if p == PropertyCaller.ATTACKER:
        return ['attacker']
    if p == PropertyCaller.ALL:
        return ['owner', 'user', 'attacker']
    assert p == PropertyCaller.ANY
    return ['user']


def generate_unit_test(test_contract: str, filename: str,
                       unit_tests: List[Property], output_dir: Path,
                       addresses: Addresses, assert_message: str = ''):
    """
    Generate unit tests files
    :param test_contract:
    :param filename:
    :param unit_tests:
    :param output_dir:
    :param addresses:
    :param assert_message:
    :return:
    """
    content = f'{test_contract} = artifacts.require("{test_contract}");\n\n'
    content += f'contract("{test_contract}", accounts => {{\n'

    content += f'\tlet owner = "{addresses.owner}";\n'
    content += f'\tlet user = "{addresses.user}";\n'
    content += f'\tlet attacker = "{addresses.attacker}";\n'
    for unit_test in unit_tests:
        if unit_test.return_type != PropertyReturn.SUCCESS:
            continue
        content += f'\tit("{unit_test.description}", async () => {{\n'
        content += f'\t\tlet instance = await {test_contract}.deployed();\n'
        if unit_test.return_type == PropertyReturn.SUCCESS:
            callers = _extract_caller(unit_test.caller)
            for caller in callers:
                content += f'\t\tlet test_{caller} = await instance.{unit_test.name[:-2]}.call({{from: {caller}}});\n'
                if assert_message:
                    content += f'\t\tassert.equal(test_{caller}, true, "{assert_message}");\n'
                else:
                    content += f'\t\tassert.equal(test_{caller}, true);\n'
        content += '\t});\n'

    content += '});\n'

    output_dir = Path(output_dir, 'test', 'crytic')
    output_dir.mkdir(exist_ok=True)

    write_file(output_dir, filename, content)
    return output_dir


def generate_migration(test_contract: str, output_dir: Path, owner_address: str):
    """
    Generate migration file
    :param test_contract:
    :param output_dir:
    :param owner_address:
    :return:
    """
    content = f'''{test_contract} = artifacts.require("{test_contract}");
module.exports = function(deployer) {{
  deployer.deploy({test_contract}, {{from: "{owner_address}"}});
}};
'''

    output_dir = Path(output_dir, 'migrations')

    migration_files = [js_file for js_file in output_dir.iterdir() if js_file.suffix == '.js'
                       and PATTERN_TRUFFLE_MIGRATION.match(js_file.name)]

    idx = len(migration_files)
    filename = f'{idx + 1}_{test_contract}.js'
    potential_previous_filename = f'{idx}_{test_contract}.js'

    for m in migration_files:
        if m.name == potential_previous_filename:
            write_file(output_dir, potential_previous_filename, content)
            return
        if test_contract in m.name:
            logger.error(f'Potential conflicts with {m.name}')

    write_file(output_dir, filename, content)
