from loguru import logger
from slither import Slither
from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.interval import DomainVariant, IntervalAnalysis, IntervalDomain


def analyze_interval(file_path: str):
    try:

        slither = Slither(file_path)
        functions = [f for c in slither.contracts for f in c.functions if f.is_implemented]

        print(f"Analyzing {len(functions)} functions...")
        vulnerable_functions = []

        for function in functions:
            print(function)

            # Run reentrancy analysis
            engine = Engine.new(analysis=IntervalAnalysis(), functions=[function])
            engine.run_analysis()
            results = engine.result()

            for node, analysis in results.items():

                if not hasattr(analysis, "post") or not isinstance(analysis.post, IntervalDomain):
                    continue

                if analysis.post.variant != DomainVariant.STATE:
                    continue

                state = analysis.post.state

                for var_name, var_info in state.info.items():
                    if "TMP_" in var_name:
                        continue
                    print(f"{var_name}: {var_info}")
                print("--------------------------------")

        # Summary

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    analyze_interval("tests/e2e/detectors/test_data/interval/0.8.10/Args.sol")
