import logging
import sys
import os.path
import traceback

from fastText import load_model
from .encode import encode_contract

logging.basicConfig()
logger = logging.getLogger("Slither-simil")

def info(args):

    try:

        model = args.model
        if os.path.isfile(model): 
            model = load_model(model)
        else:
            model = None

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
        
        x = (filename,contract,fname)
        y = " ".join(irs[x])

        print("Function {} in contract {} is encoded as:".format(fname, contract))
        print(y)
        if model is not None:
            fvector = model.get_sentence_vector(y)
            print(fvector)

    except Exception:
        logger.error('Error in %s' % args.filename)
        logger.error(traceback.format_exc())
        sys.exit(-1)


