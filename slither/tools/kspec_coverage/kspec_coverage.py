import glob
import json
import os
import subprocess
import traceback
from slither.tools.kspec_coverage.analysis import run_analysis

from importlib import reload

from crytic_compile import CryticCompile, compile_all
from crytic_compile.utils.zip import load_from_zip, save_to_zip
from time import sleep
from slither import Slither

def kspec_coverage(args):

    contract = args.filename
    kspec = args.kspec_proof

    print(f'Running Slither analysis')
    slither = Slither(contract)

    # Run the analysis on the k-framework
    run_analysis(slither, kspec)


