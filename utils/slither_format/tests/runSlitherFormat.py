from os import listdir
from os.path import isfile, join
import subprocess

contracts_path = "../../smart-contracts-detectors-testing/most_used/contracts/"
slither_format_output_path = "./slither_format/tests/slither_format_output_most_used_contracts/"

def analyze_contract_with_slither_format():
    for contract_file in contract_files:
        run_slither_format(contract_file)
    
def run_slither_format(contract_name):
    print("Running Slither Format on contract: " + contract_name)
    command = "python3 -m slither_format " + contracts_path+contract_name
    contract_slither_output_fd = open(slither_format_output_path+contract_name[:-21]+".txt","w+")
    contract_slither_output_fd.write("Command run: " + command + "\n\n")
    contract_slither_output_fd.flush()
    result = subprocess.run(command, shell=True, stdout=contract_slither_output_fd, stderr=contract_slither_output_fd)
    contract_slither_output_fd.close()

if __name__ == "__main__":
    contract_files = [f for f in listdir(contracts_path) if f.endswith(".sol")]
    print("Number of contract files: " + str(len(contract_files)))
    analyze_contract_with_slither_format()
