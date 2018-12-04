def intersection_predecessor(node):
    if not node.fathers:
        return set()
    ret = node.fathers[0].dominators
    for pred in node.fathers[1:]:
        ret = ret.intersection(pred.dominators)
    return ret

def compute_dominators(nodes):
    '''
        Naive implementation of Cooper, Harvey, Kennedy algo
        See 'A Simple,Fast Dominance Algorithm'

        Compute strict domniators
    '''
    changed = True

    for n in nodes:
        n.dominators = set(nodes)

    while changed:
        changed = False

        for node in nodes:
            new_set = intersection_predecessor(node).union({node})
            if new_set != node.dominators:
                node.dominators = new_set
                changed = True

    # compute immediate dominator
    for node in nodes:
        all_dom = []
        for dominator in node.dominators:
            doms = list(dominator.dominators)
            doms.remove(dominator)
            all_dom = all_dom + doms
        idom = [d for d in all_dom if all_dom.count(d) == 1]
        assert len(idom)<=1
        if idom:
            node.immediate_dominator = idom[0]
            idom[0].dominator_successors.add(node)



def compute_dominance_frontier(nodes):
    '''
        Naive implementation of Cooper, Harvey, Kennedy algo
        See 'A Simple,Fast Dominance Algorithm'

        Compute dominance frontier
    '''
    for node in nodes:
        if len(node.fathers) >= 2:
            for father in node.fathers:
                runner = father
                while runner != node.immediate_dominator:
                    runner.dominance_frontier = runner.dominance_frontier.union({node})
                    runner = runner.immediate_dominator


