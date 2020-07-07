import argparse
import logging
import sys
import traceback
import operator
import numpy as np
from crytic_compile import compile_all

from .model      import load_model
from .encode     import encode_contract_test, load_and_encode, parse_target
from .cache      import save_cache
from .similarity import similarity

logger = logging.getLogger("Slither-simil")

def test(args):

    try:
        model = args.model
        model = load_model(model)
        filename = args.filename
        contract, fname = parse_target(args.fname) 
        infile = args.input
        ntop = args.ntop

        if filename is None or fname is None or infile is None:
            logger.error('The test mode requires filename, contract, fname and input parameters.')
            sys.exit(-1)
        
        compilation = compile_all(filename)
        for compilation_unit in compilation:

            if ('.zip' in filename):
                irs = encode_contract_test(compilation_unit, **vars(args))
            else:
                irs = encode_contract_test(compilation_unit.target, **vars(args))
            if len(irs) == 0:
                sys.exit(-1)

            if (fname != ''):
                y = " ".join(irs[(compilation_unit.target,fname)])
                fvector = model.get_sentence_vector(y)
                cache = load_and_encode(infile, model, **vars(args))
                #save_cache("cache.npz", cache)


                r = dict()
                for x,y in cache.items():
                    r[x] = similarity(fvector, y)

                r = sorted(r.items(), key=operator.itemgetter(1), reverse=True)
                logger.info("Reviewed %d functions, listing the %d most similar ones for contract %s:", len(r), ntop, next(iter(compilation_unit.filenames)).short)
                format_table = "{: <65} {: <20} {: <20} {: <10}"
                logger.info(format_table.format(*["filename", "contract", "function", "score"]))
                for x,score in r[:ntop]:
                    score = str(round(score, 3))
                    logger.info(format_table.format(*(list(x)+[score])))
            else:
                for contr_funct, intermediate_r in irs.items():
                    y = " ".join(irs[(contr_funct)])
                    fvector = model.get_sentence_vector(y)
                    cache = load_and_encode(infile, model, **vars(args))

                    r = dict()
                    for x,y in cache.items():
                        r[x] = similarity(fvector, y)

                    r = sorted(r.items(), key=operator.itemgetter(1), reverse=True)
                    logger.info("Reviewed %d functions, listing the %d most similar ones for contract %s, function %s:", len(r), ntop, next(iter(compilation_unit.filenames)).short, contr_funct[1])
                    format_table = "{: <65} {: <20} {: <20} {: <10}"
                    logger.info(format_table.format(*["filename", "contract", "function", "score"]))
                    for x,score in r[:ntop]:
                        score = str(round(score, 3))
                        logger.info(format_table.format(*(list(x)+[score])))

    except Exception:
        logger.error('Error in %s' % args.compilation_unit.target)
        logger.error(traceback.format_exc())
        sys.exit(-1)
