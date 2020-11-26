from pathlib import Path
from typing import List

from slither.tools.properties.addresses.address import Addresses
from slither.tools.properties.utils import write_file

def generate_echidna_config(output_dir: Path, addresses: Addresses) -> str:
    """
    Generate the echidna configuration file
    :param output_dir:
    :param addresses:
    :return:
    """
    content = "prefix: crytic_\n"
    content += f'deployer: "{addresses.owner}"\n'
    content += f'sender: ["{addresses.user}", "{addresses.attacker}"]\n'
    content += f'psender: "{addresses.user}"\n'
    content += "coverage: true\n"
    filename = "echidna_config.yaml"
    write_file(output_dir, filename, content)
    return filename

def generate_echidna_auto_config(output_dir: Path, addresses: List[str], init_file: str, samples_file: str) -> str:
    """
    Generate the echidna configuration file
    :param output_dir:
    :param addresses:
    :return:
    """
    content = "prefix: crytic_\n"
    content += f'sender: [' + ','.join(map(repr,addresses)) + ']\n'
    content += "coverage: true\n"
    content += "initialize: " +  init_file + "\n"
    content += "testSamples: " +  samples_file + "\n"
    content += "multi-abi: true\n"
    filename = "echidna_config.yaml"
    write_file(output_dir, filename, content)
    return filename
