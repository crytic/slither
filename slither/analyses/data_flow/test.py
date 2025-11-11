from typing import Dict, List, TYPE_CHECKING
from slither import Slither
from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis
from slither.analyses.data_flow.analyses.interval.analysis.domain import DomainVariant
from slither.analyses.data_flow.engine.engine import Engine
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.smt_solver.types import SMTVariable
from slither.core.cfg.node import Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function

if TYPE_CHECKING:
    from slither.analyses.data_flow.logger import DataFlowLogger, LogMessages


def analyze_function(
    function: Function,
    analysis: IntervalAnalysis,
    logger: "DataFlowLogger",
    LogMessages: "type[LogMessages]",
) -> None:
    """Run interval analysis on a single function."""
    logger.info(
        "Analyzing function: {function_name} ({signature})",
        function_name=function.name,
        signature=function.signature,
    )

    # Skip if function has no nodes (not implemented or abstract)
    if not function.nodes:
        logger.warning(
            LogMessages.WARNING_SKIP_NODE,
            node_id="N/A",
            reason="function has no nodes (not implemented)",
        )
        return

    # Create engine with the analysis and function
    logger.info(LogMessages.ENGINE_INIT, function_name=function.name)
    engine: Engine[IntervalAnalysis] = Engine.new(analysis=analysis, function=function)

    # Run the analysis
    logger.debug(LogMessages.ANALYSIS_START, analysis_name="IntervalAnalysis")
    engine.run_analysis()

    # Get and display results
    results: Dict[Node, AnalysisState[IntervalAnalysis]] = engine.result()
    logger.info("Analysis complete! Processed {count} nodes.", count=len(results))

    # Display results for each node
    for node, state in results.items():
        logger.debug(
            "Node {node_id} - Pre-state: {pre_state}, Post-state: {post_state}",
            node_id=node.node_id,
            pre_state=state.pre.variant,
            post_state=state.post.variant,
        )

        # Print post-state variables
        if state.post.variant == DomainVariant.STATE:
            post_state_vars: Dict[str, SMTVariable] = state.post.state.get_range_variables()

            if post_state_vars:
                # Get node's source code representation
                node_code: str = ""
                if node.expression:
                    node_code = str(node.expression)
                elif hasattr(node, "source_mapping") and node.source_mapping:
                    node_code = node.source_mapping.content.strip()
                elif str(node):
                    node_code = str(node)

                output_lines: List[str] = []

                # Add code line if available
                if node_code:
                    output_lines.append(f"\t{node_code}")

                # Add variables
                for var_name, smt_var in post_state_vars.items():
                    # Skip internal constant variables
                    if var_name.startswith("CONST_"):
                        continue

                    # Ensure we have an SMTVariable
                    if not isinstance(smt_var, SMTVariable):
                        continue

                    # Display variable name and sort
                    output_lines.append(f"\t\t{var_name}: {smt_var.sort}")

                # Print everything
                if output_lines:
                    print("\n".join(output_lines))


def main() -> None:
    # Import logger after Slither is loaded to avoid circular import issues
    from slither.analyses.data_flow.logger import get_logger, LogMessages, DataFlowLogger

    # Initialize logger
    logger: DataFlowLogger = get_logger(enable_ipython_embed=False, log_level="DEBUG")
    logger.info(LogMessages.ENGINE_START)

    # Load the Solidity contract
    contract_path: str = "../contracts/src/Assignment.sol"
    logger.info("Loading contract from: {path}", path=contract_path)
    slither: Slither = Slither(contract_path)

    # Get all contracts - try compilation_units first, then fall back to contracts
    contracts: List[Contract]
    if slither.compilation_units:
        contracts = []
        for compilation_unit in slither.compilation_units:
            contracts.extend(compilation_unit.contracts)
    else:
        contracts = slither.contracts

    if not contracts:
        logger.warning("No contracts found!")
        return

    logger.info("Found {count} contract(s)", count=len(contracts))

    # Create interval analysis (reuse for all functions)
    analysis: IntervalAnalysis = IntervalAnalysis()
    logger.info(LogMessages.ANALYSIS_START, analysis_name="IntervalAnalysis")

    # Analyze all contracts and functions
    for contract in contracts:
        logger.info("Processing contract: {contract_name}", contract_name=contract.name)

        # Get all functions (including modifiers if needed)
        functions: List[Function] = contract.functions_and_modifiers_declared

        # Filter to only implemented, non-constructor functions
        implemented_functions: List[Function] = [
            f for f in functions if f.is_implemented and not f.is_constructor
        ]

        if not implemented_functions:
            logger.warning(
                "No implemented functions found in {contract_name}", contract_name=contract.name
            )
            continue

        logger.info(
            "Found {count} implemented function(s) in {contract_name}",
            count=len(implemented_functions),
            contract_name=contract.name,
        )

        # Analyze each function
        for function in implemented_functions:
            try:
                analyze_function(function, analysis, logger, LogMessages)
            except Exception as e:
                logger.exception(
                    LogMessages.ERROR_ANALYSIS_FAILED,
                    error=str(e),
                    function_name=function.name,
                    embed_on_error=False,
                )

    logger.info(LogMessages.ENGINE_COMPLETE)


if __name__ == "__main__":
    main()
