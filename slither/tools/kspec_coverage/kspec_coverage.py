from slither.tools.kspec_coverage.analysis import run_analysis
from slither import Slither

def kspec_coverage(args):

    contract = args.contract
    kspec = args.kspec

    print(f'Running Slither analysis')
    slither = Slither(contract)

    # Run the analysis on the k-framework
    run_analysis(slither, kspec)


