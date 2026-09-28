from dataclasses import dataclass
from collections import deque, OrderedDict

from backend import SimulatedBackend


@dataclass
class CacheStatistics:
    hits: int = 0
    misses: int = 0

    @property
    def total_requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0

        return self.hits / self.total_requests


class FIFOCache:
    def __init__(
        self,
        capacity: int,
        backend: SimulatedBackend,
    ) -> None:
        if capacity <= 0:
            raise ValueError("Cache capacity must be greater than zero.")

        self.capacity = capacity
        self.backend = backend

        self._cache: dict[str, str] = {}
        self._order: deque[str] = deque()

        self.statistics = CacheStatistics()

    def get(self, ne_name: str) -> str:
        # Cache hit
        if ne_name in self._cache:
            self.statistics.hits += 1
            return self._cache[ne_name]

        # Cache miss
        self.statistics.misses += 1
        software_version = self.backend.fetch(ne_name)

        # Cache is full -> remove oldest entry
        if len(self._cache) >= self.capacity:
            oldest = self._order.popleft()
            del self._cache[oldest]

        # Add new entry
        self._cache[ne_name] = software_version
        self._order.append(ne_name)

        return software_version

    def clear(self) -> None:
        self._cache.clear()
        self._order.clear()
        self.statistics = CacheStatistics()

    def contents(self) -> list[str]:
        return list(self._order)

class LRUCache:
    def __init__(
        self,
        capacity: int,
        backend: SimulatedBackend,
    ) -> None:
        if capacity <= 0:
            raise ValueError("Cache capacity must be greater than zero.")

        self.capacity = capacity
        self.backend = backend

        self._cache: OrderedDict[str, str] = OrderedDict()

        self.statistics = CacheStatistics()

    def get(self, ne_name: str) -> str:
        # Cache hit
        if ne_name in self._cache:
            self.statistics.hits += 1

            # Mark entry as most recently used
            self._cache.move_to_end(ne_name)

            return self._cache[ne_name]

        # Cache miss
        self.statistics.misses += 1
        software_version = self.backend.fetch(ne_name)

        # Cache is full -> remove least recently used entry
        if len(self._cache) >= self.capacity:
            self._cache.popitem(last=False)

        # Newly inserted entry is the most recently used one
        self._cache[ne_name] = software_version

        return software_version

    def clear(self) -> None:
        self._cache.clear()
        self.statistics = CacheStatistics()

    def contents(self) -> list[str]:
        return list(self._cache.keys())