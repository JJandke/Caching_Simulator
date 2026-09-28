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