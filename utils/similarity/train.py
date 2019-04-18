import argparse
import logging
import sys
import traceback
import operator

from fastText import train_unsupervised
from .encode import encode_contract, load_contracts

logger = logging.getLogger("crytic-pred")

def train(args):

    try:
        model_filename = args.model
        solc = args.solc
        dirname = args.input

        if dirname is None:
            logger.error('The train mode requires the directory parameter.')
            sys.exit(-1)

        contracts = load_contracts(dirname)
        with open("data.txt", 'w') as f:
            for contract in contracts: 
                for function,ir in encode_contract(contract,solc).items():
                    if ir != []:
                        f.write(" ".join(ir)+"\n")
    
        model = train_unsupervised(input='data.txt', model='skipgram')
        model.save_model(model_filename)
        print(model.get_words())
 
    except Exception:
        logger.error('Error in %s' % args.filename)
        logger.error(traceback.format_exc())
        sys.exit(-1)
