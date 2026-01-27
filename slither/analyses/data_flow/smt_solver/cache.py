"""
Cache for SMT solver range queries to avoid redundant computations.
"""

from typing import Dict, Tuple, Optional, Any
from collections import OrderedDict
import hashlib


class RangeQueryCache:
    """
    LRU cache for variable range queries.

    Caches the results of min/max range queries to avoid redundant
    SMT solver invocations when the same variable is queried with
    the same constraint context.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of entries to cache (LRU eviction)
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, Tuple[Optional[Any], Optional[Any]]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _compute_key(self, variable_id: str, constraints: Tuple[str, ...]) -> str:
        """
        Compute a cache key from variable ID and constraint context.

        Args:
            variable_id: Unique identifier for the variable
            constraints: Tuple of constraint string representations

        Returns:
            Cache key string
        """
        # Create a hash of the constraints for compact key
        constraints_str = "|".join(sorted(constraints))
        constraints_hash = hashlib.sha256(constraints_str.encode()).hexdigest()[:16]
        return f"{variable_id}:{constraints_hash}"

    def get(
        self, variable_id: str, constraints: Tuple[str, ...]
    ) -> Optional[Tuple[Optional[Any], Optional[Any]]]:
        """
        Retrieve cached range result.

        Args:
            variable_id: Variable identifier
            constraints: Tuple of constraint strings

        Returns:
            (min_value, max_value) tuple if cached, None if not found
        """
        key = self._compute_key(variable_id, constraints)
        if key in self._cache:
            self._hits += 1
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]
        self._misses += 1
        return None

    def put(
        self,
        variable_id: str,
        constraints: Tuple[str, ...],
        min_value: Optional[Any],
        max_value: Optional[Any],
    ) -> None:
        """
        Store range result in cache.

        Args:
            variable_id: Variable identifier
            constraints: Tuple of constraint strings
            min_value: Minimum value (None if UNSAT)
            max_value: Maximum value (None if UNSAT)
        """
        key = self._compute_key(variable_id, constraints)

        # If already exists, move to end
        if key in self._cache:
            self._cache.move_to_end(key)

        self._cache[key] = (min_value, max_value)

        # Evict oldest if over capacity
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with hits, misses, size, and hit_rate
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "hit_rate": round(hit_rate, 2),
        }

    def reset_stats(self) -> None:
        """Reset hit/miss counters."""
        self._hits = 0
        self._misses = 0
