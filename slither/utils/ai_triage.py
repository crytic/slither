"""
AI-powered false positive filtering using Claude.

This module provides functionality to filter Slither detector results
using LLM-based analysis to identify likely false positives.

Uses the Anthropic SDK with:
- Prompt caching for the system prompt (reduces costs ~90% for repeated calls)
- Batch API for processing multiple results efficiently
- Token counting to estimate costs before sending
"""

import hashlib
import json
import logging
import os
import re
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING, Any

from slither.utils.command_line import defaults_flag_in_config

if TYPE_CHECKING:
    from anthropic import Anthropic
    from slither.core.slither_core import SlitherCore
    from slither.detectors.abstract_detector import AbstractDetector

logger = logging.getLogger("Slither")

CACHE_DIR = Path("slither_ai_triage/")


def init_parser(parser: ArgumentParser) -> None:
    """
    Initialize CLI arguments for AI triage features.

    Args:
        parser: ArgumentParser to add arguments to
    """
    group = parser.add_argument_group("AI Triage (requires ANTHROPIC_API_KEY)")

    group.add_argument(
        "--ai-triage",
        help="Enable AI-powered false positive filtering (requires Anthropic API key)",
        action="store_true",
        default=defaults_flag_in_config["ai_triage"],
    )

    group.add_argument(
        "--ai-triage-model",
        help="Claude model to use for triage (default: claude-sonnet-4-5-20250929)",
        action="store",
        default=defaults_flag_in_config["ai_triage_model"],
    )

    group.add_argument(
        "--ai-triage-log",
        help="Log AI triage prompts and responses (in crytic_export/ai_triage/)",
        action="store_true",
        default=defaults_flag_in_config["ai_triage_log"],
    )

    group.add_argument(
        "--no-ai-triage-cache",
        help="Disable caching of AI triage results",
        action="store_false",
        dest="ai_triage_cache",
        default=defaults_flag_in_config["ai_triage_cache"],
    )

    group.add_argument(
        "--ai-triage-all",
        help="Triage all detectors, not just those with TRIAGE_PROMPT configured",
        action="store_false",
        dest="ai_triage_only_configured",
        default=defaults_flag_in_config["ai_triage_only_configured"],
    )


def anthropic_module() -> Any:
    """
    Return the anthropic module if available and configured.

    Returns:
        The anthropic module, or None if unavailable or not configured.
    """
    try:
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key is None:
            logger.info(
                "Please provide an Anthropic API Key in ANTHROPIC_API_KEY "
                "(https://console.anthropic.com/account/keys)"
            )
            return None
        return anthropic
    except ImportError:
        logger.info("Anthropic SDK was not installed")
        logger.info('Run "pip install anthropic"')
        return None


def get_cache_key(detector_name: str, result_id: str, source_hash: str) -> str:
    """
    Generate a cache key for a triage result.

    Args:
        detector_name: Name of the detector
        result_id: Unique ID of the result
        source_hash: Hash of relevant source code

    Returns:
        SHA256 hash to use as cache key
    """
    key_data = f"{detector_name}:{result_id}:{source_hash}"
    return hashlib.sha256(key_data.encode()).hexdigest()


def load_cached_triage(cache_key: str) -> dict | None:
    """
    Load a cached triage result if available.

    Args:
        cache_key: The cache key to look up

    Returns:
        Cached triage result dict, or None if not cached
    """
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, encoding="utf8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def save_cached_triage(cache_key: str, result: dict) -> None:
    """
    Save a triage result to cache.

    Args:
        cache_key: The cache key to store under
        result: The triage result to cache
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    try:
        with open(cache_file, "w", encoding="utf8") as f:
            json.dump(result, f, indent=2)
    except OSError as e:
        logger.warning(f"Failed to cache triage result: {e}")


def log_triage(filename: str, content: str) -> None:
    """
    Log triage prompt/response to file.

    Args:
        filename: Filename to write to
        content: Content to log
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    log_file = CACHE_DIR / filename
    with open(log_file, "a", encoding="utf8") as f:
        f.write(content)
        f.write("\n---\n")


def build_system_prompt() -> str:
    """Build the system prompt for Claude."""
    return """You are an expert Solidity security researcher triaging Slither static analysis results.

Your task is to analyze detector findings and classify them as true positives or false positives.

Guidelines:
- A TRUE POSITIVE is a real security issue or code quality problem that should be addressed
- A FALSE POSITIVE is a finding that is technically flagged but is not actually a problem because:
  - The code has sufficient protections elsewhere
  - The pattern is intentional and safe in context
  - The detector's heuristics don't apply to this specific case

When analyzing:
1. Carefully read the detector description and what it's looking for
2. Examine the source code context provided
3. Consider the contract's apparent purpose and design
4. Look for mitigating factors that make the finding not actionable

Respond with a JSON object containing:
- "classification": "true_positive" or "false_positive"
- "confidence": "high", "medium", or "low"
- "reasoning": A brief explanation (1-3 sentences) of your classification"""


def build_user_prompt(
    detector: "AbstractDetector",
    result: dict,
    source_context: str,
) -> str:
    """
    Build the user prompt for a single result.

    Args:
        detector: The detector instance that produced the result
        result: The result dict to analyze
        source_context: Relevant source code context

    Returns:
        The formatted user prompt
    """
    prompt_parts = [
        f"## Detector: {detector.ARGUMENT}",
        f"**Impact**: {result.get('impact', 'Unknown')} | "
        f"**Confidence**: {result.get('confidence', 'Unknown')}",
        "",
        "### What this detector checks for:",
        detector.WIKI_DESCRIPTION,
        "",
        "### Known exploit scenario:",
        detector.WIKI_EXPLOIT_SCENARIO if detector.WIKI_EXPLOIT_SCENARIO else "N/A",
        "",
        "### Recommendation:",
        detector.WIKI_RECOMMENDATION,
    ]

    if detector.TRIAGE_PROMPT:
        prompt_parts.extend(["", "### Detector-specific guidance:", detector.TRIAGE_PROMPT])

    prompt_parts.extend(
        [
            "",
            "### Finding:",
            result.get("description", "No description"),
            "",
            "### Source Code Context:",
            "```solidity",
            source_context,
            "```",
            "",
            "Classify this finding as true_positive or false_positive.",
        ]
    )

    return "\n".join(prompt_parts)


def extract_source_context(result: dict, slither_core: "SlitherCore") -> str:
    """
    Extract relevant source code context from a result.

    Args:
        result: The result dict containing elements with source mappings
        slither_core: The SlitherCore instance with source code access

    Returns:
        Concatenated source code context (max ~2000 chars)
    """
    contexts = []
    max_total_length = 2000

    for element in result.get("elements", []):
        source_mapping = element.get("source_mapping", {})
        filename = source_mapping.get("filename_absolute")
        start = source_mapping.get("start")
        length = source_mapping.get("length")

        if not filename or start is None or length is None:
            continue

        # Validate start and length are non-negative integers
        if not isinstance(start, int) or not isinstance(length, int):
            continue

        if filename not in slither_core.source_code:
            continue

        source = slither_core.source_code[filename]
        source_len = len(source)

        # Safe bounds calculation
        context_start = max(0, start - 50)
        context_end = min(source_len, start + length + 50)

        try:
            source_bytes = source.encode("utf8")
            context = source_bytes[context_start:context_end].decode("utf8", errors="replace")
            contexts.append(context)
        except (UnicodeDecodeError, IndexError):
            continue

        if sum(len(c) for c in contexts) > max_total_length:
            break

    return "\n...\n".join(contexts) if contexts else "Source code not available"


# Pricing per million tokens (as of 2025)
# https://platform.claude.com/docs/en/about-claude/pricing
MODEL_PRICING: dict[str, dict[str, float]] = {
    # Latest 4.5 models
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0, "cache_read": 0.30},
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0, "cache_read": 0.10},
    "claude-opus-4-5-20251101": {"input": 5.0, "output": 25.0, "cache_read": 0.50},
    # Legacy 4.x models
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0, "cache_read": 0.30},
    "claude-opus-4-20250514": {"input": 15.0, "output": 75.0, "cache_read": 1.50},
    "claude-opus-4-1-20250805": {"input": 15.0, "output": 75.0, "cache_read": 1.50},
}

# Fallback pricing for unknown models (use Sonnet 4.5 pricing as default)
DEFAULT_PRICING: dict[str, float] = {"input": 3.0, "output": 15.0, "cache_read": 0.30}


def _calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
) -> float:
    """
    Calculate the cost in USD for API usage.

    Args:
        model: Model name
        input_tokens: Number of input tokens (non-cached)
        output_tokens: Number of output tokens
        cache_read_tokens: Number of tokens read from cache

    Returns:
        Cost in USD
    """
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)
    cost = (
        (input_tokens / 1_000_000) * pricing["input"]
        + (output_tokens / 1_000_000) * pricing["output"]
        + (cache_read_tokens / 1_000_000) * pricing["cache_read"]
    )
    return cost


def _triage_single(
    client: "Anthropic",
    detector: "AbstractDetector",
    result: dict,
    source_context: str,
    system_prompt: str,
    model: str,
    log_prompts: bool,
) -> tuple[dict, dict]:
    """
    Triage a single result using Claude.

    Args:
        client: Anthropic client instance
        detector: The detector instance
        result: Result dict to analyze
        source_context: Source code context for the result
        system_prompt: System prompt to use
        model: Claude model name
        log_prompts: Whether to log prompts/responses

    Returns:
        Tuple of (triage result dict, usage dict with token counts)
    """
    result_id = result.get("id", "unknown")
    user_prompt = build_user_prompt(detector, result, source_context)

    if log_prompts:
        log_triage(
            f"{detector.ARGUMENT}_{result_id[:8]}_prompt.txt",
            f"System:\n{system_prompt}\n\nUser:\n{user_prompt}",
        )

    response = client.messages.create(
        model=model,
        max_tokens=500,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = response.content[0].text

    if log_prompts:
        log_triage(
            f"{detector.ARGUMENT}_{result_id[:8]}_response.txt",
            response_text,
        )

    # Extract token usage from response
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cache_read_tokens": getattr(response.usage, "cache_read_input_tokens", 0) or 0,
    }

    return _parse_triage_response(response_text), usage


def triage_results(
    detector: "AbstractDetector",
    results: list[dict],
    slither_core: "SlitherCore",
    model: str,
    use_cache: bool = True,
    log_prompts: bool = False,
) -> list[dict]:
    """
    Triage a list of results using Claude.

    Uses prompt caching for the system prompt to reduce costs on repeated calls.

    Args:
        detector: The detector instance
        results: List of result dicts to triage
        slither_core: The SlitherCore instance
        model: Claude model name to use
        use_cache: Whether to use file-based caching
        log_prompts: Whether to log prompts/responses

    Returns:
        Filtered list of results (false positives removed)
    """
    anthropic = anthropic_module()
    if anthropic is None:
        logger.warning("AI triage unavailable, returning all results")
        return results

    client = anthropic.Anthropic()
    system_prompt = build_system_prompt()
    filtered_results = []

    # Token tracking
    total_input_tokens = 0
    total_output_tokens = 0
    total_cache_read_tokens = 0
    api_calls = 0

    # Pre-process: check cache and prepare uncached results
    uncached_items: list[tuple[dict, str, str]] = []  # (result, source_context, cache_key)
    cached_count = 0

    for result in results:
        result_id = result.get("id", "unknown")
        source_context = extract_source_context(result, slither_core)
        source_hash = hashlib.sha256(source_context.encode()).hexdigest()[:16]
        cache_key = get_cache_key(detector.ARGUMENT, result_id, source_hash)

        if use_cache:
            cached = load_cached_triage(cache_key)
            if cached:
                cached_count += 1
                if cached.get("classification") == "true_positive":
                    result["ai_triage"] = cached
                    filtered_results.append(result)
                else:
                    logger.info(
                        f"AI triage (cached) filtered: {detector.ARGUMENT} - {result_id[:8]} "
                        f"({cached.get('reasoning', 'no reason')})"
                    )
                continue

        uncached_items.append((result, source_context, cache_key))

    # Process uncached items
    for result, source_context, cache_key in uncached_items:
        result_id = result.get("id", "unknown")

        try:
            triage_result, usage = _triage_single(
                client=client,
                detector=detector,
                result=result,
                source_context=source_context,
                system_prompt=system_prompt,
                model=model,
                log_prompts=log_prompts,
            )

            # Accumulate token usage
            api_calls += 1
            total_input_tokens += usage["input_tokens"]
            total_output_tokens += usage["output_tokens"]
            total_cache_read_tokens += usage["cache_read_tokens"]

            if use_cache:
                save_cached_triage(cache_key, triage_result)

            if triage_result.get("classification") == "true_positive":
                result["ai_triage"] = triage_result
                filtered_results.append(result)
            else:
                logger.info(
                    f"AI triage filtered: {detector.ARGUMENT} - {result_id[:8]} "
                    f"({triage_result.get('reasoning', 'no reason')})"
                )

        except Exception as e:
            logger.warning(f"AI triage failed for {result_id}: {e}")
            # On failure, keep the result (conservative approach)
            filtered_results.append(result)

    # Log token usage and cost summary
    if api_calls > 0:
        total_cost = _calculate_cost(
            model, total_input_tokens, total_output_tokens, total_cache_read_tokens
        )
        logger.info(
            f"AI triage for {detector.ARGUMENT}: {api_calls} API calls, "
            f"{cached_count} cached locally | "
            f"Tokens: {total_input_tokens:,} input, {total_output_tokens:,} output, "
            f"{total_cache_read_tokens:,} cache read | "
            f"Cost: ${total_cost:.4f}"
        )

    return filtered_results


def _parse_triage_response(response_text: str) -> dict:
    """
    Parse Claude's response into a structured dict.

    Args:
        response_text: Raw response text from Claude

    Returns:
        Parsed triage result dict
    """
    try:
        json_match = re.search(r"\{[^{}]*\}", response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except json.JSONDecodeError:
        pass

    result: dict[str, str] = {
        "classification": "true_positive",
        "confidence": "low",
        "reasoning": "Failed to parse response",
    }

    text_lower = response_text.lower()
    if "false_positive" in text_lower or "false positive" in text_lower:
        result["classification"] = "false_positive"
    if "true_positive" in text_lower or "true positive" in text_lower:
        result["classification"] = "true_positive"

    if "reasoning" in text_lower:
        lines = response_text.split("\n")
        for line in lines:
            if "reasoning" in line.lower():
                result["reasoning"] = line.split(":", 1)[-1].strip().strip('"')
                break

    return result
