import csv
from pathlib import Path

from statistics import mean, stdev
from backend import SimulatedBackend
from caches import FIFOCache, LRUCache
from workload import WorkloadGenerator, WorkloadType


# ---------------------------------------------------------
# Experiment configuration
# ---------------------------------------------------------

DATASET = "data/network_elements.csv"
RESULT_FILE = "results/cache_results.csv"
SUMMARY_FILE = "results/cache_summary.csv"

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

def save_summary(
    results: list[dict],
    output_file: str,
) -> None:
    """
    Calculates aggregated FIFO/LRU results for each workload type
    and cache capacity and writes them to a CSV file.
    """

    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary_rows = []

    for workload_type in WorkloadType:

        for capacity in CACHE_CAPACITIES:

            fifo_results = [
                result
                for result in results
                if (
                    result["workload_type"] == workload_type.value
                    and result["capacity"] == capacity
                    and result["strategy"] == FIFOCache.__name__
                )
            ]

            lru_results = [
                result
                for result in results
                if (
                    result["workload_type"] == workload_type.value
                    and result["capacity"] == capacity
                    and result["strategy"] == LRUCache.__name__
                )
            ]

            # Ensure that both strategies contain the same seeds.
            fifo_by_seed = {
                result["seed"]: result
                for result in fifo_results
            }

            lru_by_seed = {
                result["seed"]: result
                for result in lru_results
            }

            assert fifo_by_seed.keys() == lru_by_seed.keys()

            seeds = sorted(fifo_by_seed.keys())

            fifo_hit_rates = [
                fifo_by_seed[seed]["hit_rate"]
                for seed in seeds
            ]

            lru_hit_rates = [
                lru_by_seed[seed]["hit_rate"]
                for seed in seeds
            ]

            differences = [
                lru_by_seed[seed]["hit_rate"]
                - fifo_by_seed[seed]["hit_rate"]
                for seed in seeds
            ]

            summary_rows.append({
                "workload_type": workload_type.value,
                "capacity": capacity,

                "fifo_mean_hit_rate": mean(fifo_hit_rates),
                "fifo_sd_hit_rate": stdev(fifo_hit_rates),

                "lru_mean_hit_rate": mean(lru_hit_rates),
                "lru_sd_hit_rate": stdev(lru_hit_rates),

                # Stored as percentage points.
                "mean_difference_pp": mean(differences) * 100,

                "lru_better_seeds": sum(
                    difference > 0
                    for difference in differences
                ),

                "equal_seeds": sum(
                    difference == 0
                    for difference in differences
                ),

                "fifo_better_seeds": sum(
                    difference < 0
                    for difference in differences
                ),

                "fifo_mean_external_requests": mean(
                    result["external_requests"]
                    for result in fifo_results
                ),

                "lru_mean_external_requests": mean(
                    result["external_requests"]
                    for result in lru_results
                ),
            })

    fieldnames = [
        "workload_type",
        "capacity",
        "fifo_mean_hit_rate",
        "fifo_sd_hit_rate",
        "lru_mean_hit_rate",
        "lru_sd_hit_rate",
        "mean_difference_pp",
        "lru_better_seeds",
        "equal_seeds",
        "fifo_better_seeds",
        "fifo_mean_external_requests",
        "lru_mean_external_requests",
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
        writer.writerows(summary_rows)


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

def print_strategy_comparison(results: list[dict]) -> None:
    """
    Compares FIFO and LRU across seeds.

    For each workload type and cache capacity, the function reports:
        - mean hit rate for FIFO and LRU
        - sample standard deviation of the hit rates
        - mean paired LRU-FIFO difference
        - number of seeds for which LRU was better, equal, or worse
    """

    print()
    print("=" * 110)
    print("FIFO vs. LRU comparison across seeds")
    print("=" * 110)

    print(
        f"{'Workload':<20}"
        f"{'Capacity':<10}"
        f"{'FIFO Mean':<12}"
        f"{'FIFO SD':<12}"
        f"{'LRU Mean':<12}"
        f"{'LRU SD':<12}"
        f"{'Mean Δ':<12}"
        f"{'LRU >':<8}"
        f"{'Equal':<8}"
        f"{'FIFO >':<8}"
    )

    print("-" * 110)

    for workload_type in WorkloadType:

        for capacity in CACHE_CAPACITIES:

            fifo_by_seed = {}
            lru_by_seed = {}

            for result in results:

                if (
                    result["workload_type"] == workload_type.value
                    and result["capacity"] == capacity
                ):

                    if result["strategy"] == FIFOCache.__name__:
                        fifo_by_seed[result["seed"]] = result["hit_rate"]

                    elif result["strategy"] == LRUCache.__name__:
                        lru_by_seed[result["seed"]] = result["hit_rate"]

            # Both strategies must have exactly the same seeds.
            assert fifo_by_seed.keys() == lru_by_seed.keys()

            seeds = sorted(fifo_by_seed.keys())

            fifo_rates = [
                fifo_by_seed[seed]
                for seed in seeds
            ]

            lru_rates = [
                lru_by_seed[seed]
                for seed in seeds
            ]

            differences = [
                lru_by_seed[seed] - fifo_by_seed[seed]
                for seed in seeds
            ]

            lru_better = sum(
                difference > 0
                for difference in differences
            )

            equal = sum(
                difference == 0
                for difference in differences
            )

            fifo_better = sum(
                difference < 0
                for difference in differences
            )

            fifo_mean = mean(fifo_rates)
            lru_mean = mean(lru_rates)

            fifo_sd = stdev(fifo_rates)
            lru_sd = stdev(lru_rates)

            mean_difference = mean(differences)

            print(
                f"{workload_type.value:<20}"
                f"{capacity:<10}"
                f"{fifo_mean:<12.2%}"
                f"{fifo_sd:<12.2%}"
                f"{lru_mean:<12.2%}"
                f"{lru_sd:<12.2%}"
                f"{mean_difference * 100:<+12.2f}"
                f"{lru_better:<8}"
                f"{equal:<8}"
                f"{fifo_better:<8}"
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

    capacity_10_results = [
        result
        for result in results
        if result["capacity"] == 10
    ]

    for result in capacity_10_results:
        assert result["hits"] == 40
        assert result["misses"] == 10
        assert result["external_requests"] == 10
        assert result["hit_rate"] == 0.8

    # ---------------------------------------------------------
    # Save and display results
    # ---------------------------------------------------------

    save_results(
        results,
        RESULT_FILE,
    )

    save_summary(
        results,
        SUMMARY_FILE,
    )

    print("=" * 78)
    print("Experiment completed")
    print("=" * 78)

    print(f"Total runs:   {len(results)}")
    print(f"Raw results:  {RESULT_FILE}")
    print(f"Summary:      {SUMMARY_FILE}")

    print_summary(results)
    print(print_strategy_comparison(results))


if __name__ == "__main__":
    main()