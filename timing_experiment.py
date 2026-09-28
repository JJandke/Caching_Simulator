import csv
import time
from pathlib import Path
from statistics import mean, stdev

from backend import SimulatedBackend
from caches import FIFOCache, LRUCache
from workload import WorkloadGenerator, WorkloadType


# ---------------------------------------------------------
# Experiment configuration
# ---------------------------------------------------------

DATASET = "data/network_elements.csv"

RESULT_FILE = "results/timing_results.csv"
SUMMARY_FILE = "results/timing_summary.csv"

# SEEDS = range(1, 11)
# CACHE_CAPACITIES = [3, 5, 7, 10]

## Testing values for development
SEEDS = range(1, 2)
CACHE_CAPACITIES = [3]
REPETITIONS = 3

CACHE_STRATEGIES = [
    FIFOCache,
    LRUCache,
]

# REPETITIONS = 30

# 1.239 s / 100
EXTERNAL_REQUEST_DELAY = 0.01239

TIMING_MODES = {
    "simulated_external": EXTERNAL_REQUEST_DELAY,
    "cache_only": 0.0,
}


def run_timed_experiment(
    workload,
    cache_class,
    capacity: int,
    request_delay: float,
) -> dict:
    """
    Executes one complete workload and measures its elapsed
    wall-clock execution time.
    """

    backend = SimulatedBackend(
        DATASET,
        request_delay=request_delay,
    )

    cache = cache_class(
        capacity=capacity,
        backend=backend,
    )

    start = time.perf_counter()

    for ne_name in workload.requests:
        cache.get(ne_name)

    end = time.perf_counter()

    elapsed_time = end - start

    # Validate run
    assert (
        cache.statistics.hits + cache.statistics.misses
        == len(workload.requests)
    )

    assert (
        cache.statistics.misses
        == backend.request_count
    )

    return {
        "execution_time_s": elapsed_time,
        "hits": cache.statistics.hits,
        "misses": cache.statistics.misses,
        "external_requests": backend.request_count,
    }


def save_results(
    results: list[dict],
    output_file: str,
) -> None:

    output_path = Path(output_file)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "timing_mode",
        "workload_type",
        "seed",
        "capacity",
        "strategy",
        "repetition",
        "request_delay_s",
        "hits",
        "misses",
        "external_requests",
        "execution_time_s",
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


def create_summary(
    results: list[dict],
) -> list[dict]:

    summary = []

    for timing_mode in TIMING_MODES:

        for workload_type in WorkloadType:

            for capacity in CACHE_CAPACITIES:

                for cache_class in CACHE_STRATEGIES:

                    matching = [
                        result
                        for result in results
                        if (
                            result["timing_mode"] == timing_mode
                            and result["workload_type"]
                            == workload_type.value
                            and result["capacity"] == capacity
                            and result["strategy"]
                            == cache_class.__name__
                        )
                    ]

                    times = [
                        result["execution_time_s"]
                        for result in matching
                    ]

                    summary.append({
                        "timing_mode": timing_mode,
                        "workload_type": workload_type.value,
                        "capacity": capacity,
                        "strategy": cache_class.__name__,
                        "runs": len(times),
                        "mean_execution_time_s": mean(times),
                        "sd_execution_time_s": stdev(times),
                        "min_execution_time_s": min(times),
                        "max_execution_time_s": max(times),
                    })

    return summary


def save_summary(
    summary: list[dict],
    output_file: str,
) -> None:

    output_path = Path(output_file)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "timing_mode",
        "workload_type",
        "capacity",
        "strategy",
        "runs",
        "mean_execution_time_s",
        "sd_execution_time_s",
        "min_execution_time_s",
        "max_execution_time_s",
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
        writer.writerows(summary)


def print_summary(
    summary: list[dict],
) -> None:

    print()
    print("=" * 105)
    print("Timing results")
    print("=" * 105)

    for timing_mode in TIMING_MODES:

        print()
        print(timing_mode)
        print("-" * 105)

        print(
            f"{'Workload':<20}"
            f"{'Capacity':<10}"
            f"{'Strategy':<12}"
            f"{'Mean [ms]':<14}"
            f"{'SD [ms]':<14}"
            f"{'Min [ms]':<14}"
            f"{'Max [ms]':<14}"
        )

        print("-" * 105)

        for row in summary:

            if row["timing_mode"] != timing_mode:
                continue

            print(
                f"{row['workload_type']:<20}"
                f"{row['capacity']:<10}"
                f"{row['strategy']:<12}"
                f"{row['mean_execution_time_s'] * 1000:<14.3f}"
                f"{row['sd_execution_time_s'] * 1000:<14.3f}"
                f"{row['min_execution_time_s'] * 1000:<14.3f}"
                f"{row['max_execution_time_s'] * 1000:<14.3f}"
            )


def main():

    # ---------------------------------------------------------
    # Load available NEs
    # ---------------------------------------------------------

    dataset_backend = SimulatedBackend(
        DATASET,
        request_delay=0,
    )

    generator = WorkloadGenerator()

    results = []

    total_runs = (
        len(TIMING_MODES)
        * len(list(WorkloadType))
        * len(SEEDS)
        * len(CACHE_CAPACITIES)
        * len(CACHE_STRATEGIES)
        * REPETITIONS
    )

    current_run = 0

    print("=" * 78)
    print("Starting timing experiment")
    print("=" * 78)
    print(f"Total timed runs: {total_runs}")
    print()

    # ---------------------------------------------------------
    # Execute timing experiment
    # ---------------------------------------------------------

    for timing_mode, request_delay in TIMING_MODES.items():

        for workload_type in WorkloadType:

            for seed in SEEDS:

                # Generate workload once for this seed/type.
                workload = generator.generate(
                    network_elements=dataset_backend.network_elements,
                    workload_type=workload_type,
                    seed=seed,
                )

                for capacity in CACHE_CAPACITIES:

                    for cache_class in CACHE_STRATEGIES:

                        for repetition in range(1, REPETITIONS + 1):

                            measurement = run_timed_experiment(
                                workload=workload,
                                cache_class=cache_class,
                                capacity=capacity,
                                request_delay=request_delay,
                            )

                            results.append({
                                "timing_mode": timing_mode,
                                "workload_type": workload_type.value,
                                "seed": seed,
                                "capacity": capacity,
                                "strategy": cache_class.__name__,
                                "repetition": repetition,
                                "request_delay_s": request_delay,
                                **measurement,
                            })

                            current_run += 1

                            if current_run % 100 == 0:
                                print(
                                    f"Completed "
                                    f"{current_run}/{total_runs} runs"
                                )

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    assert len(results) == total_runs

    # ---------------------------------------------------------
    # Save results
    # ---------------------------------------------------------

    save_results(
        results,
        RESULT_FILE,
    )

    summary = create_summary(results)

    save_summary(
        summary,
        SUMMARY_FILE,
    )

    print()
    print("=" * 78)
    print("Timing experiment completed")
    print("=" * 78)
    print(f"Total runs:   {len(results)}")
    print(f"Raw results:  {RESULT_FILE}")
    print(f"Summary:      {SUMMARY_FILE}")

    print_summary(summary)


if __name__ == "__main__":
    main()