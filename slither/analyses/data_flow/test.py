from slither import Slither
from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.reentrancy import (
    DomainVariant,
    ReentrancyAnalysis,
    ReentrancyDomain,
)


def analyze_reentrancy(file_path: str):
    try:

        slither = Slither(file_path)
        functions = [f for c in slither.contracts for f in c.functions if f.is_implemented]

        print(f"Analyzing {len(functions)} functions...")
        vulnerable_functions = []

        for function in functions:

            func_name = str(function.name)

            # Run reentrancy analysis
            engine = Engine.new(analysis=ReentrancyAnalysis(), functions=[function])
            engine.run_analysis()
            results = engine.result()

            # Check for vulnerability
            is_vulnerable = False
            vulnerable_vars = []

            for node, analysis in results.items():
                if not hasattr(analysis, "post") or not isinstance(analysis.post, ReentrancyDomain):
                    continue

                if analysis.post.variant != DomainVariant.STATE:
                    continue

                state = analysis.post.state

                # Check reentrancy pattern: variable read before call AND written after
                vars_at_risk = state.storage_variables_read_before_calls.intersection(
                    state.storage_variables_written
                )

                if vars_at_risk and state.external_calls:
                    is_vulnerable = True
                    vulnerable_vars.extend([var.name for var in vars_at_risk])

            # Report results
            if is_vulnerable:
                vulnerable_functions.append(func_name)
                print(f"🚨 {func_name}: VULNERABLE - Variables: {set(vulnerable_vars)}")
            else:
                print(f"✅ {func_name}: Safe")

        # Summary
        print(f"\nResult: {len(vulnerable_functions)}/{len(functions)} functions vulnerable")
        return vulnerable_functions

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":

    analyze_reentrancy(
        "tests/e2e/detectors/test_data/reentrancy-eth/0.8.10/reentrancy_filtered_comments.sol"
    )
