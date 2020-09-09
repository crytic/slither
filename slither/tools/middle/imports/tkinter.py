import sys

try:
    import tkinter as _tk
    from tkinter import messagebox as _messagebox, ttk as _ttk
except ImportError:
    print("ERROR: in order to use middle, you need to install tkinter")
    print("On Ubuntu: \n")
    print("\tsudo apt-get install python3-tk\n")
    print("On macOS: \n")
    # TODO
    print("On Windows: \n")
    # TODO
    sys.exit(-1)

messagebox = _messagebox
tk = _tk
ttk = _ttk
