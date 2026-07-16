import sys

try:
    from fasttext import load_model
    from fasttext import train_unsupervised
except ImportError:
    print("ERROR: slither-simil requires fasttext. Install with:")
    print("  pip install slither-analyzer[simil]")
    print("  # or: uv pip install slither-analyzer[simil]")
    print("  # or add fasttext to existing install: pip install fasttext")
    sys.exit(-1)
