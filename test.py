from backend import SimulatedBackend
from caches import FIFOCache, LRUCache


requests = ["A", "B", "C", "A", "D"]


backend_fifo = SimulatedBackend(
    "data/test_network_elements.csv",
    request_delay=0,
)

fifo = FIFOCache(
    capacity=3,
    backend=backend_fifo,
)

for ne in requests:
    fifo.get(ne)

print("FIFO contents:", fifo.contents())
print("FIFO hits:", fifo.statistics.hits)
print("FIFO misses:", fifo.statistics.misses)


backend_lru = SimulatedBackend(
    "data/test_network_elements.csv",
    request_delay=0,
)

lru = LRUCache(
    capacity=3,
    backend=backend_lru,
)

for ne in requests:
    lru.get(ne)

print("LRU contents:", lru.contents())
print("LRU hits:", lru.statistics.hits)
print("LRU misses:", lru.statistics.misses)