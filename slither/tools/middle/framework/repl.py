import pickle
import re
import sys

from slither.tools.middle.framework.analyzer import Analyzer, GroupAnalyzer
from slither.tools.middle.framework.strategy import ConcreteStrategy
from slither.tools.middle.framework.util import InconsistentStateError, pickle_analyzer, unpickle_analyzer, pickle_object, unpickle_object


def main():
    down_pattern = re.compile(r'call\s+(\d+)')
    data_pattern = re.compile(r'let\s+(\d+)\s*=\s*(\d+)')
    query_pattern = re.compile(r'query\s+(\d+)')
    init_pattern = re.compile(r'init\s+(\w+)')
    show_pattern = re.compile(r'show\s+(\d+)')
    source_pattern = re.compile(r'source\s+(\d+)')
    switch_pattern = re.compile(f'switch\s+(\d+)')

    group_analyzer = GroupAnalyzer()
    analyzer = Analyzer(ConcreteStrategy(), sys.argv[1])
    group_analyzer.add_group(analyzer)

    while True:
        info = input("> ")

        match_down_pattern = down_pattern.match(info)
        match_data_pattern = data_pattern.match(info)
        match_query_pattern = query_pattern.match(info)
        match_init_pattern = init_pattern.match(info)
        match_show_pattern = show_pattern.match(info)
        match_source_pattern = source_pattern.match(info)
        match_switch_pattern = switch_pattern.match(info)

        if match_init_pattern is not None:
            name = match_init_pattern.group(1)
            # Initialize the analyzer with this function
            if analyzer.initialized:
                print("ERROR: analysis already initialized...")
                print("       Try using the 'clear' command")
            else:
                analyzer.add_function(name)

            analyzer.run_to_fixpoint()

        elif info == "clear":
            analyzer.clear()

        elif info == "graph":
            analyzer.view_digraph()

        elif info == "graph source":
            print(analyzer.get_digraph().source)

        elif info == "original":
            analyzer.overlay_graph.view_digraph()

        elif info == "solve":
            analyzer.strategy.resolve_ir_vars()
            analyzer.run_to_fixpoint()

            # Get the digraph so that the call nodes are labeled. This is kind
            # of hacky, but its really just a UI issue.
            analyzer.get_digraph()

        elif info == "begin":
            pickle_analyzer(analyzer, 'previous.pickle')

            commands = []
            while True:
                command = input("    >> ")
                if command == "commit":
                    break
                commands.append(command)

            for command in commands:
                if data_pattern.match(command) is None:
                    print("ERROR: cannot process {} because it is not a let binding".format(command))
                    print("Rolling back...")
                    analyzer = unpickle_analyzer('previous.pickle')
                    break

                symvar_id, value = data_pattern.match(command).group(1, 2)
                symvar_id, value = int(symvar_id), int(value)
                symvar = analyzer.get_symvar_from_id(symvar_id)

                try:
                    analyzer.set_sym_var_value(symvar, value)
                    analyzer.run_to_fixpoint()
                except InconsistentStateError as e:
                    print("ERROR: {}".format(e))
                    print("Rolling back...")
                    analyzer = unpickle_analyzer('previous.pickle')
                    break

        elif match_down_pattern is not None:
            pickle_analyzer(analyzer, 'previous.pickle')

            # Down call the given function by id number.
            callsite_id = match_down_pattern.group(1)

            try:
                analyzer.down_call(int(callsite_id))
                analyzer.run_to_fixpoint()
            except InconsistentStateError as e:
                print("ERROR: {}".format(e))
                print("Rolling back...")
                analyzer = unpickle_analyzer('previous.pickle')

        elif match_data_pattern is not None:
            pickle_analyzer(analyzer, 'previous.pickle')

            # Provide new data for a certain labeled symbolic variable.
            #   e.g. let [id] = [value]
            symvar_id, value = match_data_pattern.group(1, 2)
            symvar_id, value = int(symvar_id), int(value)
            symvar = analyzer.get_symvar_from_id(symvar_id)

            try:
                analyzer.set_sym_var_value(symvar, value)
                analyzer.run_to_fixpoint()
            except InconsistentStateError as e:
                print("ERROR: {}".format(e))
                print("Rolling back...")
                analyzer = unpickle_analyzer('previous.pickle')

        elif match_query_pattern is not None:
            # Query the value of a certain labeled symbolic variable.
            #   e.g. query [id]
            symvar_id = match_query_pattern.group(1)
            symvar_id = int(symvar_id)
            symvar = analyzer.get_symvar_from_id(symvar_id)
            print(analyzer.get_sym_var_value(symvar))

        elif match_show_pattern is not None:
            func_id = int(match_show_pattern.group(1))
            func = next((x for x in analyzer.live_functions if x.id == func_id), None)
            if func is None:
                print("ERROR: could not find function with FID {}".format(func_id))
                continue
            func.print_human_readable_ir()

        elif match_source_pattern is not None:
            func_id = int(match_source_pattern.group(1))
            func = next((x for x in analyzer.live_functions if x.id == func_id), None)
            if func is None:
                print("ERROR: could not find function with FID {}".format(func_id))
                continue
            func.print_human_readable_source()

        # Right now we only allow a single state to be saved.
        elif info == "save":
            pickle_object(group_analyzer, 'save_group.pickle')
            pickle_object(analyzer, 'save_analyzer.pickle')
            continue

        elif info == "load":
            group_analyzer = unpickle_object('save_group.pickle')
            analyzer = unpickle_object('save_analyzer.pickle')
            continue

        elif info == "list":
            print(analyzer.get_function_id_list())

        elif info == "groups":
            group_analyzer.print_groups()

        elif match_switch_pattern is not None:
            analyzer_id = int(match_switch_pattern.group(1))
            analyzer = group_analyzer.find_by_id(analyzer_id)

        elif info == "prepend":
            # We are doing an up call
            group_analyzer.remove_by_id(analyzer.id)
            new_analyzers = analyzer.up_call()
            group_analyzer.extend(new_analyzers)

            if not new_analyzers:
                print("FATAL: No call sites available, RIP")
                exit(-1)

            analyzer = new_analyzers[0]

        else:
            print("ERROR: did not recognize command")


if __name__ == '__main__':
    main()
