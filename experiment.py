from backend import SimulatedBackend
from caches import FIFOCache, LRUCache
from workload import WorkloadGenerator, WorkloadType


DATASET = "data/network_elements.csv"

SEED = 1
CACHE_CAPACITIES = [3, 5, 7, 10]
WORKLOAD_TYPE = WorkloadType.STABLE_LOCALITY


def run_experiment(
    workload,
    cache_class,
    capacity: int,
) -> dict:
    """
    Executes one workload using one cache strategy and capacity.

    Returns the resulting cache statistics.
    """

    backend = SimulatedBackend(
        DATASET,
        request_delay=0,
    )

    cache = cache_class(
        capacity=capacity,
        backend=backend,
    )

    # Execute workload
    for ne_name in workload.requests:
        cache.get(ne_name)

    # Validate experiment results
    assert (
        cache.statistics.hits + cache.statistics.misses
        == len(workload.requests)
    )

    assert (
        cache.statistics.misses
        == backend.request_count
    )

    return {
        "strategy": cache_class.__name__,
        "capacity": capacity,
        "hits": cache.statistics.hits,
        "misses": cache.statistics.misses,
        "hit_rate": cache.statistics.hit_rate,
        "external_requests": backend.request_count,
    }


def main():
    # ---------------------------------------------------------
    # Generate one fixed workload
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
    # Run experiments
    # ---------------------------------------------------------

    results = []

    for capacity in CACHE_CAPACITIES:

        fifo_result = run_experiment(
            workload=workload,
            cache_class=FIFOCache,
            capacity=capacity,
        )

        lru_result = run_experiment(
            workload=workload,
            cache_class=LRUCache,
            capacity=capacity,
        )

        results.append(fifo_result)
        results.append(lru_result)

    # ---------------------------------------------------------
    # Print configuration
    # ---------------------------------------------------------

    print("=" * 76)
    print("Experiment configuration")
    print("=" * 76)

    print(f"Workload type:  {workload.workload_type.value}")
    print(f"Seed:           {workload.seed}")
    print(f"Requests:       {len(workload.requests)}")
    print(f"Working set:    {len(workload.working_set)} NEs")
    print(f"Cache sizes:    {CACHE_CAPACITIES}")

    # ---------------------------------------------------------
    # Print results
    # ---------------------------------------------------------

    print()
    print("=" * 76)
    print("Results")
    print("=" * 76)

    print(
        f"{'Capacity':<10}"
        f"{'Strategy':<12}"
        f"{'Hits':<8}"
        f"{'Misses':<10}"
        f"{'Hit Rate':<12}"
        f"{'External':<10}"
    )

    print("-" * 76)

    for result in results:
        print(
            f"{result['capacity']:<10}"
            f"{result['strategy']:<12}"
            f"{result['hits']:<8}"
            f"{result['misses']:<10}"
            f"{result['hit_rate']:<12.2%}"
            f"{result['external_requests']:<10}"
        )


if __name__ == "__main__":
    main()