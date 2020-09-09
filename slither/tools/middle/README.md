# Solar

Solar is a static analysis framework that tries to bring meaning to the phrase "middle out analysis". Solar prides itself on providing context-free interactive analysis.

## Build Instructions

1. Clone a modified version of slither located here: [git@github.com:aaronyoo/slither.git](git@github.com:aaronyoo/slither.git)
2. Do the normal developer setup. Directions are in the slither wiki: [link](https://github.com/crytic/slither/wiki/Developer-installation). Copy pasting works fine for me.
3. Checkout the dev branch.
4. Now clone the slither labs repo into the top level directory of the slither repo and checkout the `middle` branch.

```
git clone git@github.com:trailofbits/slither-labs.git
cd slither-labs
git checkout middle
```

5. Go back to the top level slither directory and export the current directory and the middle out analysis directory into your PYTHONPATH. This must be done from the top level directory because we are using relative paths.
```
export PYTHONPATH=./:./slither-labs/middle_out_analysis
```

6. Install some dependencies:
    - `pip3 install graphviz`
    - make sure that `solc` is installed

7. Run the gui which takes in the sol file for analysis. If you wish to do a project wide analysis just pass in the project folder as an argument instead (only truffle projects are supported as of now).

```
python3 slither-labs/middle_out_analysis/framework/gui.py slither-labs/middle_out_analysis/tests/demo.sol
```

```
// slither-labs/middle_out_analysis/tests/demo.sol
contract Contract {
    function f(int x) public returns (int) {
        int i = x;
        if (i == 0) {
            i = g(x);
        } else {
            i = 7;
        }
        return i;
    }


    function g(int x) public returns (int) {
        return x + h(x);
    }

    function h(int x) public returns (int) {
        return x + 3;
    }
}
```

---

## Directory Structure

```
middle_out_analysis
├── README.md
├── demo-truffle   (demo project that can be used with Solar)
├── framework      (contains the analyzer and strategies)
├── overlay        (contains overlay node types and transformations)
└── tests          (a collection of test programs)
```

```
framework
├── __init__.py
├── analyzer.py    (the main code for the analyzer)
├── function.py    (the main code for the analysis function)
├── gui.py         (the main code for the gui)
├── repl.py        (legacy code for the repl)
├── strategy.py    (all the strategies)
├── tokens.py      (token types used to print to gui)
├── util.py        (utility functions for analysis)
└── var.py         (variable structure for ConcreteStrategy)
```

```
overlay
├── ast
│   ├── call.py         (call instruction)
│   ├── function.py     (overlay function containing instructions)
│   ├── graph.py        (overlay graph containing overlay functions)
│   ├── ite.py          (if then else instruction)
│   ├── node.py         (OverlayNode, a base class for all other instructions)
│   └── unwrap.py       (unwrap instruction to emulate a break)
├── construction.py     (simple constructor)
├── transform.py        (all transformation logic)
└── util.py             (some transformation utitlity functions)
```

---

## Architecture

At the current moment there are really two parts to Solar. First, there are the transformations that are applied to a Slither instance to create and OverlayGraph. Second, there is an analyzer that takes the OverlayGraph and governs the inference, up-calling, and down-calling that is necessary for Solar to work.

In order to make primitive operations efficient at scale, Solar relies on a transformation pass that has the overarching goal of turning SlithIR into a Datalog-like form. There are two main parts to this transformation that sport functions of the same name:

1. Outline all conditionals
2. Compress phi nodes

The outline all conditionals step renders a flat looking control flow by removing all conditionals. The compress phi nodes step fixes up some inconsistencies when returning values. A lot of work during these steps goes into trying to preserve the SSA properties of the SlithIR. The entire point of doing this transformation is to have only linear control flow with conditional calls. This makes the SlithIR more Datalog-like. Thus, it becomes possible to reason about any function as an unordered bag of statements (similar to how Datalog works) governed by data dependencies. The OverlayGraph created by this transformation phase is a collection of OverlayFunctions which are each in turn a collection of OverlayNodes that can either point to an underlying SlithIR node, or exist by themselves. The OverlayNodes that exist by themselves have been introduced by the pass to capture some special semantics (ITE, Unwrap, etc).

Once the transformation is done we get a bunch of linear functions. Some functions are new because they were outlined in the previous pass. The OverlayGraph has as view_digraph() function that allows one to see the structure of the graph overall. Now, there were some design decisions that were deemed to be mistakes in hindsight when developing the analyzer, but for the most updated type of design, reference the Constraint Strategy. In this design paradigm the strategy is actually responsible for telling the analyzer when it is done solving. This means that a lot of the computation is actually delegated to the strategy. To control a strategy (in terms of presentation) there are a few flags in the base strategy class.
