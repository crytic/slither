import logging
import sys
import traceback

from fastText import load_model
from .encode import encode_contract

logging.basicConfig()
logger = logging.getLogger("Slither-simil")

def info(args):

    try:
        model = args.model
        model = load_model(model)
        filename = args.filename
        contract = args.contract
        solc = args.solc
        fname = args.fname
        if filename is None and contract is None and fname is None:
            print(args.model,"uses the following words:")
            for word in model.get_words():
                print(word)
            sys.exit(0)

        if filename is None or contract is None or fname is None:
            logger.error('The encode mode requires filename, contract and fname parameters.')
            sys.exit(-1)

        irs = encode_contract(filename, solc=solc)
        if len(irs) == 0:
            sys.exit(-1)

        x = "-".join([filename,contract,fname])
        y = " ".join(irs[x])
        
        fvector = model.get_sentence_vector(y)
        print("Function {} in contract {} is encoded as:".format(fname, contract))
        print(y)
        print(fvector)

    except Exception:
        logger.error('Error in %s' % args.filename)
        logger.error(traceback.format_exc())
        sys.exit(-1)


