import logging
import operator
import sys
import traceback

from slither.tools.similarity.encode import encode_contract, load_and_encode, parse_target
from slither.tools.similarity.model import load_model
from slither.tools.similarity.similarity import similarity

logger = logging.getLogger("Slither-simil")


def test(args):

    try:
        model = args.model
        model = load_model(model)
        filename = args.filename
        contract, fname = parse_target(args.fname)
        infile = args.input
        ntop = args.ntop

        if filename is None or contract is None or fname is None or infile is None:
            logger.error("The test mode requires filename, contract, fname and input parameters.")
            sys.exit(-1)

        irs = encode_contract(filename, **vars(args))
        if len(irs) == 0:
            sys.exit(-1)

        y = " ".join(irs[(filename, contract, fname)])

        fvector = model.get_sentence_vector(y)
        cache = load_and_encode(infile, model, **vars(args))
        # save_cache("cache.npz", cache)

        r = dict()
        for x, y in cache.items():
            r[x] = similarity(fvector, y)

        r = sorted(r.items(), key=operator.itemgetter(1), reverse=True)
        logger.info("Reviewed %d functions, listing the %d most similar ones:", len(r), ntop)
        format_table = "{: <65} {: <20} {: <20} {: <10}"
        logger.info(format_table.format(*["filename", "contract", "function", "score"]))
        for x, score in r[:ntop]:
            score = str(round(score, 3))
            logger.info(format_table.format(*(list(x) + [score])))

    except Exception:  # pylint: disable=broad-except
        logger.error("Error in %s" % args.filename)
        logger.error(traceback.format_exc())
        sys.exit(-1)
