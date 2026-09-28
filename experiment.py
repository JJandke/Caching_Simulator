from backend import SimulatedBackend
from caches import FIFOCache, LRUCache
from workload import WorkloadGenerator, WorkloadType


DATASET = "data/network_elements.csv"

SEED = 1
CACHE_CAPACITY = 3
WORKLOAD_TYPE = WorkloadType.STABLE_LOCALITY


def run_cache(cache, workload):
    """
    Executes all requests of one workload using the given cache.
    """

    for ne_name in workload.requests:
        cache.get(ne_name)


def main():
    # ---------------------------------------------------------
    # Generate workload
    # ---------------------------------------------------------

    workload_backend = SimulatedBackend(
        DATASET,
        request_delay=0,
    )

    generator = WorkloadGenerator()

    workload = generator.generate(
        network_elements=workload_backend.network_elements,
        workload_type=WORKLOAD_TYPE,
        seed=SEED,
    )

    # ---------------------------------------------------------
    # FIFO
    # ---------------------------------------------------------

    fifo_backend = SimulatedBackend(
        DATASET,
        # TODO: Enable sleep for actual testing. Just disabled for debugging as of now.
        request_delay=0,
    )

    fifo = FIFOCache(
        capacity=CACHE_CAPACITY,
        backend=fifo_backend,
    )

    run_cache(fifo, workload)

    # ---------------------------------------------------------
    # LRU
    # ---------------------------------------------------------

    lru_backend = SimulatedBackend(
        DATASET,
        request_delay=0,
    )

    lru = LRUCache(
        capacity=CACHE_CAPACITY,
        backend=lru_backend,
    )

    run_cache(lru, workload)

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------

    print("=" * 60)
    print("Experiment configuration")
    print("=" * 60)

    print(f"Workload type:  {workload.workload_type.value}")
    print(f"Seed:           {workload.seed}")
    print(f"Cache capacity: {CACHE_CAPACITY}")
    print(f"Requests:       {len(workload.requests)}")
    print(f"Working set:    {len(workload.working_set)} NEs")

    print()

    print("=" * 60)
    print("FIFO")
    print("=" * 60)

    print(f"Hits:              {fifo.statistics.hits}")
    print(f"Misses:            {fifo.statistics.misses}")
    print(f"Hit rate:          {fifo.statistics.hit_rate:.2%}")
    print(f"External requests: {fifo_backend.request_count}")

    print()

    print("=" * 60)
    print("LRU")
    print("=" * 60)

    print(f"Hits:              {lru.statistics.hits}")
    print(f"Misses:            {lru.statistics.misses}")
    print(f"Hit rate:          {lru.statistics.hit_rate:.2%}")
    print(f"External requests: {lru_backend.request_count}")


if __name__ == "__main__":
    main()