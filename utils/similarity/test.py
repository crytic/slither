import argparse
import logging
import sys
import traceback
import operator
import numpy as np

from fastText import load_model
from .encode import encode_contract, load_contracts
from .cache import load_cache, save_cache
from .similarity import similarity

logger = logging.getLogger("Slither-simil")

def test(args):

    try:
        model = args.model
        model = load_model(model)
        filename = args.filename
        contract = args.contract
        fname = args.fname
        solc = args.solc
        infile = args.input
        ext = args.filter

        if filename is None or contract is None or fname is None or infile is None:
            logger.error('The test mode requires filename, contract, fname and input parameters.')
            sys.exit(-1)

        irs = encode_contract(filename,solc=solc)
        if len(irs) == 0:
            sys.exit(-1)

        y = " ".join(irs[(filename,contract,fname)])
        
        fvector = model.get_sentence_vector(y)
        cache = load_cache(infile, model, ext=ext, solc=solc)
        #save_cache("cache.npz", cache)

        r = dict()
        for x,y in cache.items():
            r[x] = similarity(fvector, y)

        r = sorted(r.items(), key=operator.itemgetter(1), reverse=True)
        for x,score in r[:10]:
            print(x,score)

    except Exception:
        logger.error('Error in %s' % args.filename)
        logger.error(traceback.format_exc())
        sys.exit(-1)
