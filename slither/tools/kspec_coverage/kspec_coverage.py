from slither.tools.kspec_coverage.analysis import run_analysis
from slither import Slither

def kspec_coverage(args):

    contract = args.contract
    kspec = args.kspec

    slither = Slither(contract)

    # Run the analysis on the Klab specs
    run_analysis(args, slither, kspec)


