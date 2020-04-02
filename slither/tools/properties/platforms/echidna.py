from pathlib import Path

from slither.tools.properties.addresses.address import Addresses
from slither.tools.properties.utils import write_file


def generate_echidna_config(output_dir: Path, addresses: Addresses) -> str:
    """
    Generate the echidna configuration file
    :param output_dir:
    :param addresses:
    :return:
    """
    content = 'prefix: crytic_\n'
    content += f'deployer: "{addresses.owner}"\n'
    content += f'sender: ["{addresses.user}", "{addresses.attacker}"]\n'
    content += 'coverage: true\n'
    filename = 'echidna_config.yaml'
    write_file(output_dir, filename, content, allow_overwrite=False)
    return filename
