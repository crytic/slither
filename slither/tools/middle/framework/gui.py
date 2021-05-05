import sys
import re
from collections import defaultdict

from slither.slithir.variables import Constant

from slither.tools.middle.framework.analyzer import Analyzer
from slither.tools.middle.framework.strategy import (
    ConcreteStrategy,
    SymbolicStrategy,
    ConstraintStrategy,
)
from slither.tools.middle.framework.tokens import NewLine, Variable, Indent
from slither.tools.middle.framework.util import (
    pickle_object,
    unpickle_object,
    InconsistentStateError,
)
from slither.tools.middle.overlay.util import resolve_nearest_concrete_parent
from slither.tools.middle.imports.tkinter import tk, ttk


class GUI:
    def __init__(self):
        self.analyzer = Analyzer(ConcreteStrategy(), sys.argv[1])

        self.instances = []

        self.top = top = tk.Tk()
        top.title("Solar")

        self.frm_left = frm_left = tk.Frame(top, padx=5, pady=5)
        frm_left.pack(side=tk.LEFT, fill=tk.BOTH)

        self.frm_list = frm_list = tk.Frame(frm_left, padx=5, pady=5)
        self.lbl_func = lbl_func = tk.Label(frm_list, text="Functions")
        self.bx_func = bx_func = tk.Listbox(frm_list)
        frm_list.pack(side=tk.TOP, fill=tk.Y)
        lbl_func.pack(side=tk.TOP, fill=tk.X)
        bx_func.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.frm_strat = frm_strat = tk.Frame(frm_left, padx=5, pady=5)
        self.lbl_strat = lbl_strat = tk.Label(frm_strat, text="Strategy")
        self.bx_strat = bx_strat = tk.Listbox(frm_strat)
        frm_strat.pack(side=tk.TOP, fill=tk.BOTH)
        lbl_strat.pack(side=tk.TOP, fill=tk.X)
        bx_strat.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        bx_strat.insert(tk.END, "Concrete")
        bx_strat.insert(tk.END, "Symbolic")
        bx_strat.insert(tk.END, "Constraint")
        self.selected_strategy = ConcreteStrategy

        def bind_strategy(event):
            name = self.bx_strat.get(tk.ANCHOR)
            if name == "Concrete":
                self.selected_strategy = ConcreteStrategy
            elif name == "Symbolic":
                self.selected_strategy = SymbolicStrategy
            elif name == "Constraint":
                self.selected_strategy = ConstraintStrategy

        bx_strat.bind("<Double-Button>", bind_strategy)

        self.note = note = ttk.Notebook(top)
        note.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        for func in self.analyzer.overlay_graph.functions:
            # Only allow the selection of non-outlined functions.
            if func.func is not None:
                bx_func.insert(tk.END, func.name)

        def bind_start_func(event):
            name = self.bx_func.get(tk.ANCHOR)
            analyzer = Analyzer(self.selected_strategy(), sys.argv[1])
            parent = ttk.Frame(note)
            gui = AnalysisGUI(self, parent, analyzer, name)
            self.instances.append(gui)
            note.add(parent, text=str(self.instances.index(gui)))

        bx_func.bind("<Double-Button>", bind_start_func)

    def add_analyzer(self, analyzer):
        parent = ttk.Frame(self.note)
        gui = AnalysisGUI(self, parent, analyzer, analyzer.root.under.name)
        self.instances.append(gui)
        self.note.add(parent, text=str(self.instances.index(gui)))

    def close_analysis(self, analysis_gui):
        # Forget the current tab
        self.note.forget(self.note.select())

        self.instances.remove(analysis_gui)


class AnalysisGUI:
    def __init__(self, gui, parent, analyzer, name):

        self.top = top = parent
        self.gui = gui
        self.analyzer = analyzer
        self.analyzer.add_function(name)

        self.frm_toolbar = frm_toolbar = tk.Frame(top, padx=5, pady=5)
        self.btn_graph = tk.Button(
            frm_toolbar,
            text="Graph",
            padx=5,
            pady=5,
            width=10,
            command=lambda: self.analyzer.view_digraph(),
        )
        self.btn_graph.pack(side=tk.LEFT, fill=tk.X)
        self.btn_graph = tk.Button(
            frm_toolbar,
            text="Original",
            padx=5,
            pady=5,
            width=10,
            command=lambda: self.analyzer.overlay_graph.view_digraph(),
        )
        self.btn_graph.pack(side=tk.LEFT, fill=tk.X)
        self.btn_refresh = tk.Button(
            frm_toolbar, text="Refresh", padx=5, pady=5, width=10, command=lambda: self.refresh()
        )
        self.btn_refresh.pack(side=tk.LEFT, fill=tk.X)
        self.btn_solve = tk.Button(
            frm_toolbar, text="Simplify", padx=5, pady=5, width=10, command=self.solve
        )
        self.btn_solve.pack(side=tk.LEFT, fill=tk.X)
        self.btn_upcall = tk.Button(
            frm_toolbar, text="Up Call", padx=5, pady=5, width=10, command=self.do_up_call
        )
        self.btn_upcall.pack(side=tk.LEFT, fill=tk.X)
        self.btn_break = tk.Button(
            frm_toolbar, text="Break", padx=5, pady=5, width=10, command=self.br
        )
        self.btn_break.pack(side=tk.LEFT, fill=tk.X)
        self.btn_close = tk.Button(
            frm_toolbar, text="Close", padx=5, pady=5, width=10, command=self.close_analysis
        )
        self.btn_close.pack(side=tk.RIGHT, fill=tk.X)
        self.frm_toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        if isinstance(self.analyzer.strategy, ConstraintStrategy):
            self.btn_constrain = tk.Button(
                frm_toolbar, text="Constrain", padx=5, pady=5, width=10, command=self.constrain
            )
            self.btn_constrain.pack(side=tk.LEFT, fill=tk.X)
        elif isinstance(self.analyzer.strategy, ConcreteStrategy):
            self.btn_annotate = tk.Button(
                frm_toolbar, text="Annotate", padx=5, pady=5, width=10, command=self.toggle_annotate
            )
            self.btn_annotate.pack(side=tk.RIGHT, fill=tk.X)

        # Create the source frame
        self.frm_source = frm_source = tk.Frame(top, padx=5, pady=5)

        frm_source.grid_rowconfigure(0, weight=1)
        frm_source.grid_columnconfigure(0, weight=1)

        self.hbar_source = hbar_source = tk.Scrollbar(frm_source, orient=tk.HORIZONTAL)
        hbar_source.grid(row=1, column=0, sticky=tk.E + tk.W)
        self.vbar_source = vbar_source = tk.Scrollbar(frm_source, orient=tk.VERTICAL)
        vbar_source.grid(row=0, column=1, sticky=tk.N + tk.S)

        self.canv_source = canv_source = SourceCanvas(
            self.analyzer,
            self,
            frm_source,
            width=400,
            height=400,
            bd=0,
            xscrollcommand=hbar_source.set,
            yscrollcommand=vbar_source.set,
        )
        canv_source.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)

        self.lbl_source = lbl_source = tk.Label(frm_source, text="Source")
        frm_source.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        # hbar_source.pack(side=tk.BOTTOM, fill=tk.X)
        hbar_source.config(command=canv_source.xview)
        # vbar_source.pack(side=tk.RIGHT, fill=tk.Y)
        vbar_source.config(command=canv_source.yview)
        # lbl_source.pack(side=tk.TOP, fill=tk.X)
        # canv_source.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        canv_source.config(xscrollcommand=hbar_source.set, yscrollcommand=vbar_source.set)

        # Create the ir frame
        self.frm_ir = frm_ir = tk.Frame(top, padx=5, pady=5)

        frm_ir.grid_rowconfigure(0, weight=1)
        frm_ir.grid_columnconfigure(0, weight=1)

        self.hbar_ir = hbar_ir = tk.Scrollbar(frm_ir, orient=tk.HORIZONTAL)
        hbar_ir.grid(row=1, column=0, sticky=tk.E + tk.W)
        self.vbar_ir = vbar_ir = tk.Scrollbar(frm_ir, orient=tk.VERTICAL)
        vbar_ir.grid(row=0, column=1, sticky=tk.N + tk.S)

        self.lbl_ir = lbl_ir = tk.Label(frm_ir, text="IR")
        self.canv_ir = canv_ir = ExploreCanvas(
            self.analyzer,
            self,
            frm_ir,
            width=400,
            height=400,
            bd=0,
            xscrollcommand=hbar_ir.set,
            yscrollcommand=vbar_ir.set,
        )
        canv_ir.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)

        frm_ir.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        # hbar_ir.pack(side=tk.BOTTOM, fill=tk.X)
        hbar_ir.config(command=canv_ir.xview)
        # vbar_ir.pack(side=tk.RIGHT, fill=tk.Y)
        vbar_ir.config(command=canv_ir.yview)
        # lbl_ir.pack(side=tk.TOP, fill=tk.X)
        # canv_ir.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        canv_ir.config(xscrollcommand=hbar_ir.set, yscrollcommand=vbar_ir.set)

        self.refresh()

    def get_token_list(self):
        return self.analyzer.root.to_tokens(0)

    def get_live_source_mappings(self):
        return self.analyzer.root.get_live_source_mappings()

    def solve(self):
        try:
            if self.analyzer.strategy.command_fixpoint:
                self.analyzer.strategy.run_to_fixpoint()
            else:
                self.analyzer.run_to_fixpoint()
        except InconsistentStateError as e:
            msg = str(e) + "\n"
            msg += "Trying to roll back..."
            if self.analyzer.strategy.command_fixpoint:
                msg = "WARN: cannot assure roll back due to ctypes dependency, trying best effort.."
                tk.messagebox.showerror(title="Error", message=str(e) + "\n" + msg)
                return

            tk.messagebox.showerror(title="Error", message=msg)

            # Restore the analyzer and update the analyzer for the Source and IR.
            self.refresh_analyzer(restore_analyzer())

        self.refresh()

    def refresh(self):
        self.canv_ir.render_token_list(self.get_token_list())
        self.canv_source.render_source_mappings(self.get_live_source_mappings())

    def refresh_analyzer(self, analyzer):
        self.analyzer = analyzer
        self.canv_source.analyzer = analyzer
        self.canv_ir.analyzer = analyzer

    def refresh_source_with_xref(self, xref_var):
        self.canv_source.render_source_mappings(
            self.get_live_source_mappings(), xref_ir_var=xref_var
        )

    def refresh_ir_with_xref(self, xref_var):
        self.canv_ir.render_token_list(self.get_token_list(), xref_var=xref_var)

    def do_up_call(self):
        window = UpCallDialog(self.top, self.analyzer, self)
        self.refresh()
        return

    def change_analyzer(self, analyzer):
        # Change the analyzers for all the canvases.
        self.analyzer = analyzer
        self.canv_ir.analyzer = analyzer
        self.canv_source.analyzer = analyzer

    def br(self):
        pass

    def close_analysis(self):
        self.gui.close_analysis(self)

    def constrain(self):
        window = AddConstraintDialog(self.top, self.analyzer, self)

    def toggle_annotate(self):
        self.analyzer.strategy.hide_resolved = not self.analyzer.strategy.hide_resolved
        self.refresh()


class Lexeme:
    def __init__(self, filename, curr_char, curr_line, literal):
        self.filename: str = filename
        self.curr_char: int = curr_char
        self.curr_line: int = curr_line
        self.literal: str = literal

    def __str__(self):
        return self.literal


class SourceInfo:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.files = defaultdict(list)
        self.lexemes = []

        for filename, source in analyzer.slither.source_code.items():
            current_char = 0
            current_line = 1
            for lexeme in list(filter(lambda x: x != "", re.split(r"(\W)", source))):
                l = Lexeme(filename, current_char, current_line, lexeme)
                self.files[filename].append(l)
                self.lexemes.append(l)
                current_char += len(lexeme)
                for c in lexeme:
                    if c == "\n":
                        current_line += 1
                # TODO: handle tabs here


class SourceCanvas(tk.Canvas):
    MIN_WIDTH = 50
    MIN_HEIGHT = 50

    TAG_LINENUM = "LineNum"
    TAG_XREF = "xref"
    TAG_ACTIVE = "Active"
    TAG_VAR = "variable"

    def __init__(self, analyzer, gui, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.analyzer = analyzer
        self.source_info = SourceInfo(analyzer)
        self.gui = gui
        self.current_width = self.MIN_WIDTH
        self.current_height = self.MIN_HEIGHT
        self.var_item_to_var = {}
        self.xref_item_to_bg = {}

        self.bind("<Button-1>", self.single_click)

        self.files = {}

    def render_source_mappings(self, mappings, xref_ir_var=None):
        self.clear_canvas()

        # Loop over each file the the lines that need to be printed
        for filename, d in mappings.items():

            line_num_to_func = {}
            for function, active_lines in d.items():
                # Create a dictionary that maps line numbers to functions. This map
                # also contains all of the lines that are live.
                for line in active_lines:
                    line_num_to_func[line] = function

            file_lexemes = self.source_info.files[filename]

            # Create the filename as a comment
            self.add_new_line()
            self.add_new_line()
            self.create_text(
                self.current_width, self.current_height, text="   {}".format(filename), anchor="nw"
            )
            self.add_new_line()
            self.add_new_line()

            for line_num in sorted(set([x.curr_line for x in file_lexemes])):
                # Create the line number
                line_num_item = self.create_text(
                    self.current_width,
                    self.current_height,
                    text="{}:".format(str(line_num).rjust(3)),
                    anchor="nw",
                )
                _, _, self.current_width, _ = self.bbox(line_num_item)
                self.addtag(line_num_item, self.TAG_LINENUM)
                self.add_space()

                # Everything in this line will be tagged with the line tag.
                line_tag = "line_{}".format(line_num)

                # Get the lexemes referring to the current line
                lexemes = sorted(
                    [x for x in file_lexemes if x.curr_line == line_num and x.literal != "\n"],
                    key=lambda x: x.curr_char,
                )

                for lexeme in lexemes:
                    # Create the lexeme on the canvas.
                    item = self.create_text(
                        self.current_width, self.current_height, text=lexeme.literal, anchor="nw"
                    )
                    _, _, self.current_width, _ = self.bbox(item)
                    self.addtag(item, line_tag)

                    # Check if its a variable. There is only a chance for it to be a settable variable
                    # if there is a function associated with this line.
                    if line_num in line_num_to_func:
                        function = line_num_to_func[line_num]
                        assoc_stmt = function.find_stmt_containing_source_mapping(
                            filename, lexeme.curr_char
                        )
                        if assoc_stmt is not None:
                            vars = (
                                assoc_stmt.node.variables_read
                                + assoc_stmt.node.variables_written
                                + [assoc_stmt.node.variable_declaration]
                            )
                            v = next((v for v in vars if str(v) == lexeme.literal), None)
                            if v is not None:
                                # It is a variable
                                self.addtag(item, self.TAG_VAR)
                                self.var_item_to_var[item] = v

                                # Add and xref tag if it is an xref
                                if xref_ir_var is not None and str(v) == str(
                                    xref_ir_var.non_ssa_version
                                ):
                                    self.addtag(item, self.TAG_XREF)

                self.add_new_line()

            for line_num in line_num_to_func.keys():
                for item in self.find_withtag("line_{}".format(line_num)):
                    self.addtag(item, self.TAG_ACTIVE)

        # Highlight all the line numbers.
        for line_num_item in self.find_withtag(self.TAG_LINENUM):
            self.itemconfig(line_num_item, fill="blue")

        # Put a green box around all the active or "visited" lines.
        for active_item in self.find_withtag(self.TAG_ACTIVE):
            rect = self.create_rectangle(self.bbox(active_item), fill="green", outline="")
            self.tag_lower(rect, active_item)

        # Put a purple box around all variables
        # for active_item in self.find_withtag(self.TAG_VAR):
        #     rect = self.create_rectangle(self.bbox(active_item), fill="purple", outline="")
        #     self.tag_lower(rect, active_item)

        # Highlight all variables that are xrefs.
        for xref_item in self.find_withtag(self.TAG_XREF):
            self.apply_xref_formatting(xref_item)

        # Configure the scroll region of the canvas to enable scrolling
        self.config(scrollregion=self.bbox(tk.ALL))

    def addtag(self, item, tags):
        if not isinstance(tags, tuple):
            tags = (tags,)
        self.itemconfig(item, tags=self.gettags(item) + tags)

    def clear_canvas(self):
        # Delete all items on the canvas and reset the width + height pointers.
        self.delete("all")
        self.current_width = self.MIN_WIDTH
        self.current_height = self.MIN_HEIGHT
        self.var_item_to_var.clear()
        self.xref_item_to_bg.clear()

    def add_new_line(self):
        self.current_width = self.MIN_WIDTH
        self.current_height = self.current_height + 20

    def add_space(self, tags=None):
        item = self.create_text(self.current_width, self.current_height, text=" ", anchor="nw")
        _, _, self.current_width, _ = self.bbox(item)

        if tags is not None:
            self.addtag(item, tags)

    def add_tab(self, tags=None):
        item = self.create_text(self.current_width, self.current_height, text="    ", anchor="nw")
        _, _, self.current_width, _ = self.bbox(item)

        if tags is not None:
            self.addtag(item, tags)

    def single_click(self, event):
        try:
            item = event.widget.find_withtag("current")[0]
        except IndexError:
            return
        tags = self.gettags(item)

        if self.TAG_VAR in tags:
            self.send_xref_request(event)

    def apply_xref_formatting(self, item):
        rect = self.create_rectangle(self.bbox(item), fill="orange", outline="")
        self.tag_lower(rect, item)
        self.xref_item_to_bg[item] = rect

    def remove_xref_formatting(self, item):
        self.delete(self.xref_item_to_bg[item])

    def send_xref_request(self, event):
        item = event.widget.find_withtag("current")[0]
        var = self.var_item_to_var[item]

        # Remove all the xref formatting
        for xref_item in self.find_withtag(self.TAG_XREF):
            self.dtag(xref_item, self.TAG_XREF)
            self.remove_xref_formatting(xref_item)

        # Apply xref formatting to the current variable
        self.addtag(item, self.TAG_XREF)
        self.apply_xref_formatting(item)

        self.gui.refresh_ir_with_xref(var)


class ExploreCanvas(tk.Canvas):
    MIN_WIDTH = 50
    MIN_HEIGHT = 50

    TAG_XREF = "xref"

    def __init__(self, analyzer, gui, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.gui = gui
        self.analyzer = analyzer
        self.parent = self.nametowidget(self.winfo_toplevel())
        self.current_width = self.MIN_WIDTH
        self.current_height = self.MIN_HEIGHT
        self.id_map = {}
        self.xref_item_to_bg = {}

        self.bind("<Double-1>", self.double_click)
        self.bind("<Button-1>", self.single_click)

    def render_token_list(self, tok_list, xref_var=None):
        self.clear_canvas()

        # Render all the tokens with tags that are mapped to their objects.
        for token in tok_list:
            text = token.render()
            if isinstance(token, NewLine):
                self.add_new_line()
                continue
            if isinstance(token, Indent):
                self.add_indent()
                continue

            item = self.create_text(self.current_width, self.current_height, text=text, anchor="nw")
            _, _, self.current_width, _ = self.bbox(item)
            self.id_map[item] = token
            self.add_space()
            self.itemconfig(item, tags=type(token).__name__)

            if not self.analyzer.strategy.hide_resolved and token.annotation is not None:
                annot_text = token.annotation.render()
                annot_item = self.create_text(
                    self.current_width, self.current_height, text=annot_text, anchor="nw"
                )
                _, _, self.current_width, _ = self.bbox(annot_item)
                self.id_map[annot_item] = token.annotation
                self.add_space()
                self.itemconfig(annot_item, tags=type(token.annotation).__name__)

        # Highlight all the keywords.
        for keyword in self.find_withtag("Keyword"):
            self.itemconfig(keyword, fill="blue")

        # Highlight all the variables in red and allow them to be set.
        for variable in self.find_withtag("Variable"):
            if isinstance(self.id_map[variable].var, Constant):
                # Untag because a constant is not a variable.
                self.dtag(variable, "Variable")
                continue
            self.itemconfig(variable, fill="red")

        # Highlight all the potential call sites in purple
        for call_site in self.find_withtag("CallSite"):
            self.itemconfig(call_site, fill="purple")

        # Highlight all the annotations in green
        for annotation in self.find_withtag("Annotation"):
            self.itemconfig(annotation, fill="orange")

        # Tag all the IR variables that are associated with the xref_var
        for variable in self.find_withtag("Variable"):
            token = self.id_map[variable]
            if isinstance(token.var, Constant):
                continue
            if token.var.non_ssa_version == xref_var:
                self.addtag(variable, self.TAG_XREF)
                self.apply_xref_formatting(variable)

        # Configure the scroll region of the canvas to enable scrolling
        self.config(scrollregion=self.bbox(tk.ALL))

    def add_space(self):
        # Simulates a space character by adding to the width.
        self.current_width += 8

    def add_indent(self):
        self.current_width += 8 * 4

    def add_new_line(self):
        self.current_width = self.MIN_WIDTH
        self.current_height = self.current_height + 20

    def clear_canvas(self):
        # Delete all items on the canvas and reset the width + height pointers.
        self.delete("all")
        self.current_width = self.MIN_WIDTH
        self.current_height = self.MIN_HEIGHT
        self.id_map.clear()

    def double_click(self, event):
        try:
            item = event.widget.find_withtag("current")[0]
        except IndexError:
            return
        tags = self.gettags(item)

        if "Variable" in tags:
            self.set_var_value(event)
        if "CallSite" in tags:
            self.inline_call(event)

        # Automatically simplify
        # self.gui.solve()
        self.gui.refresh()

    def single_click(self, event):
        try:
            item = event.widget.find_withtag("current")[0]
        except IndexError:
            return
        tags = self.gettags(item)

        if "Variable" in tags:
            self.send_xref_request(event)

    def send_xref_request(self, event):
        item = event.widget.find_withtag("current")[0]
        token = self.id_map[item]

        # Remove all the xref formatting
        for xref_item in self.find_withtag(self.TAG_XREF):
            self.dtag(xref_item, self.TAG_XREF)
            self.remove_xref_formatting(xref_item)

        # Apply xref formatting to the current variable
        self.addtag(item, self.TAG_XREF)
        self.apply_xref_formatting(item)

        self.gui.refresh_source_with_xref(token.var)

    def set_var_value(self, event):
        item = event.widget.find_withtag("current")[0]
        token = self.id_map[item]
        window = SetValueDialog(self.parent, self.analyzer, token)
        self.parent.wait_window(window)

    def inline_call(self, event):
        if not self.analyzer.strategy.command_fixpoint:
            save_analyzer(self.analyzer)
        item = event.widget.find_withtag("current")[0]
        token = self.id_map[item]

        self.analyzer.down_call(token.func, token.assoc_stmt)

    def addtag(self, item, tags):
        if not isinstance(tags, tuple):
            tags = (tags,)
        self.itemconfig(item, tags=self.gettags(item) + tags)

    def apply_xref_formatting(self, item):
        rect = self.create_rectangle(self.bbox(item), fill="orange", outline="")
        self.tag_lower(rect, item)
        self.xref_item_to_bg[item] = rect

    def remove_xref_formatting(self, item):
        self.delete(self.xref_item_to_bg[item])


class SetValueDialog(tk.Toplevel):
    def __init__(self, parent, analyzer: Analyzer, variable: Variable):
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)

        self.analyzer = analyzer
        self.variable = variable

        body = tk.Frame(self)
        body.pack(padx=5, pady=5)
        self.label = label = tk.Label(body, text=str(variable.var))
        self.ty_label = ty_label = tk.Label(body, text=": " + str(variable.var.type))
        self.entry = entry = tk.Entry(body)
        self.confirm_button = confirm_button = tk.Button(body, text="Enter", command=self.cleanup)
        self.cancel_button = cancel_button = tk.Button(body, text="Cancel", command=self.cancel)
        label.pack(side="left")
        ty_label.pack(side="left")
        entry.pack(side="left")
        confirm_button.pack(side="left")
        cancel_button.pack(side="left")

        self.grab_set()

        self.value = None

    def cancel(self):
        self.grab_release()
        self.destroy()

    def cleanup(self):
        # Interpret as an int for now but that won't always be the case.
        val = self.entry.get()
        type_str = str(self.variable.var.type)

        if "int" in type_str:
            try:
                self.value = int(val)
            except ValueError:
                tk.messagebox.showerror("Error", '"{}" is not a valid integer'.format(val))
                return
        elif type_str == "bool":
            if val == "True":
                self.value = True
            elif val == "False":
                self.value = False
            else:
                tk.messagebox.showerror(
                    "Error", '"{}" is not a valid boolean. Try True or False'.format(val)
                )
                return

        if not self.analyzer.strategy.command_fixpoint:
            save_analyzer(self.analyzer)

        try:
            if self.analyzer.strategy.set_value_in_strategy:
                self.analyzer.strategy.set_value(
                    self.analyzer.get_var_value(self.variable.var, self.variable.func), self.value
                )
            else:
                self.analyzer.set_var_value(
                    self.variable.var, self.variable.func, self.value, deduce=True
                )
        except InconsistentStateError as e:
            tk.messagebox.showerror("Error", str(e))
            if not self.analyzer.strategy.command_fixpoint:
                self.analyzer = restore_analyzer()

        self.grab_release()
        self.destroy()


class AddConstraintDialog(tk.Toplevel):
    def __init__(self, parent, analyzer: Analyzer, gui):
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.analyzer = analyzer
        self.value = None
        self.gui = gui

        body = tk.Frame(self)
        body.pack(padx=5, pady=5)
        self.label = label = tk.Label(body, text="Add Constraint: ")
        self.entry = entry = tk.Entry(body)
        self.confirm_button = confirm_button = tk.Button(body, text="Enter", command=self.cleanup)
        self.cancel_button = cancel_button = tk.Button(body, text="Cancel", command=self.cancel)
        label.pack(side="left")
        entry.pack(side="left")
        confirm_button.pack(side="left")
        cancel_button.pack(side="left")

    def cancel(self):
        self.grab_release()
        self.destroy()

    def cleanup(self):
        s = self.entry.get()
        self.value = s

        self.analyzer.strategy.add_constraint(s)
        self.gui.solve()
        self.cancel()


class UpCallDialog(tk.Toplevel):
    def __init__(self, parent, analyzer: Analyzer, gui):
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.analyzer = analyzer
        self.value = None
        self.gui = gui
        self.text_to_callsite = {}

        body = tk.Frame(self)
        body.pack(padx=5, pady=5)
        self.label = label = tk.Label(body, text="Choose Up-Call Destination")
        self.callsites = callsites = tk.Listbox(body)
        self.cancel_button = cancel_button = tk.Button(body, text="Cancel", command=self.cancel)
        label.pack(side=tk.TOP)
        callsites.pack(side=tk.BOTTOM)

        # Populate the listbox with the callsites
        for func, callsite in self.analyzer.find_up_call_sites(self.analyzer.root):
            name = resolve_nearest_concrete_parent(self.analyzer.overlay_graph, func).name
            self.text_to_callsite[name] = (func, callsite)
            callsites.insert(tk.END, name)

        def bind_select_callsite(event):
            name = self.callsites.get(tk.ANCHOR)
            func, callsite = self.text_to_callsite[name]
            if not self.analyzer.strategy.command_fixpoint:
                save_analyzer(self.analyzer)
            try:
                self.analyzer.up_call_choose(func, callsite)
            except InconsistentStateError as e:
                tk.messagebox.showerror("Error", str(e))
                if not self.analyzer.strategy.command_fixpoint:
                    self.gui.refresh_analyzer(restore_analyzer())
            self.gui.solve()
            self.cancel()

        callsites.bind("<Double-Button>", bind_select_callsite)

    def cancel(self):
        self.grab_release()
        self.destroy()


def save_analyzer(analyzer):
    pickle_object(analyzer, "save_analyzer.pickle")


def restore_analyzer() -> Analyzer:
    return unpickle_object("save_analyzer.pickle")
