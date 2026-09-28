import csv
from pathlib import Path

from backend import SimulatedBackend
from caches import FIFOCache, LRUCache
from workload import WorkloadGenerator, WorkloadType


# ---------------------------------------------------------
# Experiment configuration
# ---------------------------------------------------------

DATASET = "data/network_elements.csv"
RESULT_FILE = "results/cache_results.csv"

SEEDS = range(1, 11)
CACHE_CAPACITIES = [3, 5, 7, 10]

CACHE_STRATEGIES = [
    FIFOCache,
    LRUCache,
]


def run_experiment(
    workload,
    cache_class,
    capacity: int,
) -> dict:
    """
    Executes one workload using one cache strategy and capacity.

    No artificial delay is used at this stage because this experiment
    evaluates cache hits, misses, and external requests only.
    """

    backend = SimulatedBackend(
        DATASET,
        request_delay=0,
    )

    cache = cache_class(
        capacity=capacity,
        backend=backend,
    )

    for ne_name in workload.requests:
        cache.get(ne_name)

    # -----------------------------------------------------
    # Validate result
    # -----------------------------------------------------

    assert (
        cache.statistics.hits + cache.statistics.misses
        == len(workload.requests)
    )

    assert (
        cache.statistics.misses
        == backend.request_count
    )

    return {
        "workload_type": workload.workload_type.value,
        "seed": workload.seed,
        "capacity": capacity,
        "strategy": cache_class.__name__,
        "hits": cache.statistics.hits,
        "misses": cache.statistics.misses,
        "hit_rate": cache.statistics.hit_rate,
        "external_requests": backend.request_count,
    }


def save_results(
    results: list[dict],
    output_file: str,
) -> None:
    """
    Writes all individual experiment results to a CSV file.
    """

    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "workload_type",
        "seed",
        "capacity",
        "strategy",
        "hits",
        "misses",
        "hit_rate",
        "external_requests",
    ]

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(results)


def print_summary(results: list[dict]) -> None:
    """
    Calculates and prints mean results across all seeds.
    """

    print()
    print("=" * 78)
    print("Mean results across seeds")
    print("=" * 78)

    for workload_type in WorkloadType:

        print()
        print(workload_type.value)
        print("-" * 78)

        print(
            f"{'Capacity':<10}"
            f"{'Strategy':<12}"
            f"{'Mean Hits':<12}"
            f"{'Mean Misses':<14}"
            f"{'Hit Rate':<12}"
            f"{'External':<10}"
        )

        print("-" * 78)

        for capacity in CACHE_CAPACITIES:

            for cache_class in CACHE_STRATEGIES:

                matching_results = [
                    result
                    for result in results
                    if (
                        result["workload_type"]
                        == workload_type.value
                        and result["capacity"]
                        == capacity
                        and result["strategy"]
                        == cache_class.__name__
                    )
                ]

                if not matching_results:
                    continue

                count = len(matching_results)

                mean_hits = (
                    sum(
                        result["hits"]
                        for result in matching_results
                    )
                    / count
                )

                mean_misses = (
                    sum(
                        result["misses"]
                        for result in matching_results
                    )
                    / count
                )

                mean_hit_rate = (
                    sum(
                        result["hit_rate"]
                        for result in matching_results
                    )
                    / count
                )

                mean_external = (
                    sum(
                        result["external_requests"]
                        for result in matching_results
                    )
                    / count
                )

                print(
                    f"{capacity:<10}"
                    f"{cache_class.__name__:<12}"
                    f"{mean_hits:<12.2f}"
                    f"{mean_misses:<14.2f}"
                    f"{mean_hit_rate:<12.2%}"
                    f"{mean_external:<10.2f}"
                )


def main():
    # ---------------------------------------------------------
    # Load available network elements
    # ---------------------------------------------------------

    backend = SimulatedBackend(
        DATASET,
        request_delay=0,
    )

    generator = WorkloadGenerator()

    results = []

    # ---------------------------------------------------------
    # Generate and execute all workloads
    # ---------------------------------------------------------

    for workload_type in WorkloadType:

        for seed in SEEDS:

            # Important:
            # Generate this workload only once.
            #
            # The same workload object is then used for every
            # capacity and both cache strategies.
            workload = generator.generate(
                network_elements=backend.network_elements,
                workload_type=workload_type,
                seed=seed,
            )

            for capacity in CACHE_CAPACITIES:

                for cache_class in CACHE_STRATEGIES:

                    result = run_experiment(
                        workload=workload,
                        cache_class=cache_class,
                        capacity=capacity,
                    )

                    results.append(result)

    # ---------------------------------------------------------
    # Validate complete experiment
    # ---------------------------------------------------------

    expected_runs = (
        len(list(WorkloadType))
        * len(SEEDS)
        * len(CACHE_CAPACITIES)
        * len(CACHE_STRATEGIES)
    )

    assert len(results) == expected_runs

    # ---------------------------------------------------------
    # Save and display results
    # ---------------------------------------------------------

    save_results(
        results,
        RESULT_FILE,
    )

    print("=" * 78)
    print("Experiment completed")
    print("=" * 78)

    print(f"Total runs:  {len(results)}")
    print(f"Result file: {RESULT_FILE}")

    print_summary(results)


if __name__ == "__main__":
    main()