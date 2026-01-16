import logging
import operator
import sys
import traceback

from slither.tools.similarity.encode import encode_contract, load_and_encode, parse_target
from slither.tools.similarity.model import load_model
from slither.tools.similarity.similarity import similarity

logger = logging.getLogger("Slither-simil")


def test(**kwargs) -> None:
    try:
        model = kwargs.get("model")
        model = load_model(model)
        filename = kwargs.get("filename")
        contract, fname = parse_target(kwargs.get("fname"))
        infile = kwargs.get("input")
        ntop = kwargs.get("ntop")

        if filename is None or contract is None or fname is None or infile is None:
            logger.error("The test mode requires filename, contract, fname and input parameters.")
            sys.exit(-1)

        irs = encode_contract(filename, **kwargs)
        if len(irs) == 0:
            sys.exit(-1)

        y = " ".join(irs[(filename, contract, fname)])

        fvector = model.get_sentence_vector(y)
        cache = load_and_encode(infile, model, **kwargs)
        # save_cache("cache.npz", cache)

        r = {}
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
        logger.error(f"Error in {kwargs.get('filename')}")
        logger.error(traceback.format_exc())
        sys.exit(-1)
