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
        threshold = args.threshold

        if filename is None or fname is None or infile is None:
            logger.error('The test mode requires filename, contract, fname and input parameters.')
            sys.exit(-1)
        
        compilation = compile_all(filename)
        for compilation_unit in compilation:
            if (isinstance(compilation_unit, list)):
                irs = encode_contract_test(compilation_unit[0], **vars(args))
            else:
                irs = encode_contract_test(compilation_unit.target, **vars(args))
            if len(irs) == 0:
                continue
                #sys.exit(-1)

            if (fname != ''):
                y = " ".join(irs[(compilation_unit.target,fname)])
                fvector = model.get_sentence_vector(y)
                cache = load_and_encode(infile, model, **vars(args))


                r = dict()
                for x,y in cache.items():
                    r[x] = similarity(fvector, y)

                r = {key: value for (key, value) in r.items() if value > 0.75 }
                r = sorted(r.items(), key=operator.itemgetter(1), reverse=True)
                if (isinstance(compilation_unit, list)):
                    logger.info("Reviewed %d functions, listing the %d most similar ones for contract %s:", len(r), ntop, next(iter(compilation_unit[0].filenames)).short)
                else:
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

                    r = {key: value for (key, value) in r.items() if value > threshold }
                    r = sorted(r.items(), key=operator.itemgetter(1), reverse=True)
                    if (len(r) != 0):
                        if (isinstance(compilation_unit, list)):
                            #logger.info("Reviewed %d functions, listing the %d most similar ones for contract %s, function %s:", len(r), ntop, next(iter(compilation_unit[0].filenames)).short, contr_funct[1])
                            scoreList = list()
                            for x,score in r[:ntop]:
                                score = str(round(score, 3))
                                scoreList.append("{}: {}".format('/'.join(e for e in list(x)), score))
                            print("{}/{}, {}".format(next(iter(compilation_unit[0].filenames)).short, contr_funct[1], ', '.join([e for e in scoreList])))
                        else:
                            #logger.info("Reviewed %d functions, listing the %d most similar ones for contract %s, function %s:", len(r), ntop, next(iter(compilation_unit.filenames)).short, contr_funct[1])
                            for x,score in r[:ntop]:
                                score = str(round(score, 3))
                                scoreList.append("{}: {}".format('/'.join(e for e in list(x)), score))
                            print("{}/{}, {}".format(next(iter(compilation_unit.filenames)).short, contr_funct[1], ', '.join([e for e in scoreList])))

                        #format_table = "{: <65} {: <65} {: <30} {: <20} {: <10}"
                        #logger.info(format_table.format(*["project_id", "filename", "contract", "function", "score"]))
                        #for x,score in r[:ntop]:
                            #score = str(round(score, 3))
                            #logger.info(format_table.format(*(list(x)+[score])))

    except Exception:
        logger.error('Error in %s' % args.compilation_unit.target)
        logger.error(traceback.format_exc())
        sys.exit(-1)
