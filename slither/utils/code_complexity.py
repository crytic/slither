# Function computing the code complexity

def compute_number_edges(function):
    """
    Compute the number of edges of the CFG
    Args:
        function (core.declarations.function.Function)
    Returns:
        int
    """
    n = 0
    for node in function.nodes:
        n += len(node.sons)
    return n


def compute_strongly_connected_components(function):
    """
        Compute strongly connected components
        Based on Kosaraju algo
        Implem follows wikipedia algo: https://en.wikipedia.org/wiki/Kosaraju%27s_algorithm#The_algorithm
    Args:
        function (core.declarations.function.Function)
    Returns:
        list(list(nodes))
    """
    visited = {n:False for n in function.nodes}
    assigned = {n:False for n in function.nodes}
    components = []
    l = []

    def visit(node):
        if not visited[node]:
            visited[node] = True
            for son in node.sons:
                visit(son)
            l.append(node)

    for n in function.nodes:
        visit(n)

    def assign(node, root):
        if not assigned[node]:
            assigned[node] = True
            root.append(node)
            for father in node.fathers:
                assign(father, root)

    for n in l:
        component = []
        assign(n, component)
        if component:
            components.append(component)

    return components

def compute_cyclomatic_complexity(function):
    """
    Compute the cyclomatic complexity of a function
    Args:
        function (core.declarations.function.Function)
    Returns:
        int
    """
    # from https://en.wikipedia.org/wiki/Cyclomatic_complexity
    # M = E - N + 2P
    # where M is the complexity
    # E number of edges
    # N number of nodes
    # P number of connected components

    E = compute_number_edges(function)
    N = len(function.nodes)
    P = len(compute_strongly_connected_components(function))
    return E - N + 2 * P
