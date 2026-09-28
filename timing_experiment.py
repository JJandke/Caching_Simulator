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

# Final experiment values:
# SEEDS = range(1, 11)
# CACHE_CAPACITIES = [3, 5, 7, 10]
# REPETITIONS = 30

# Development/test values:
SEEDS = range(1, 2)
CACHE_CAPACITIES = [3]
REPETITIONS = 3

# Cache-only timing executes the complete workload repeatedly inside
# one timed block to reduce relative timer and scheduling noise.
CACHE_ONLY_INNER_ITERATIONS = 1000

CACHE_STRATEGIES = [
    FIFOCache,
    LRUCache,
]

# Measured SSH mean: 1.239 s; simulation uses a 1:100 scaling.
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
    timing_mode: str,
) -> dict:
    """
    Execute and time one workload configuration.

    simulated_external:
        Executes one complete workload with the configured artificial
        external-request delay.

    cache_only:
        Executes the complete workload CACHE_ONLY_INNER_ITERATIONS times
        without an artificial delay and reports the average time of one
        workload. The backend is created before the timed section so CSV
        loading is excluded from the measurement.
    """

    if timing_mode == "cache_only":

        iterations = CACHE_ONLY_INNER_ITERATIONS

        # Load the dataset before timing so CSV loading is not measured.
        backend = SimulatedBackend(
            DATASET,
            request_delay=0,
        )

        start = time.perf_counter()

        for _ in range(iterations):

            # Every workload execution starts with an empty cache.
            cache = cache_class(
                capacity=capacity,
                backend=backend,
            )

            for ne_name in workload.requests:
                cache.get(ne_name)

        end = time.perf_counter()

        # Average execution time of one complete workload.
        elapsed_time = (end - start) / iterations

        # The backend counter accumulates across all inner iterations.
        assert backend.request_count == (
            cache.statistics.misses * iterations
        )

    else:

        iterations = 1

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

        assert (
            backend.request_count
            == cache.statistics.misses
        )

    # General validation: one workload always contains the same number
    # of requests, regardless of timing mode.
    assert (
        cache.statistics.hits
        + cache.statistics.misses
        == len(workload.requests)
    )

    return {
        "execution_time_s": elapsed_time,
        "hits": cache.statistics.hits,
        "misses": cache.statistics.misses,
        # Store the per-workload number for both timing modes.
        "external_requests": cache.statistics.misses,
        "inner_iterations": iterations,
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
        "inner_iterations",
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
    """
    Development summary.

    This currently summarizes all timing observations directly.
    Before the final experiment analysis, this will be replaced by
    two-stage aggregation:
        repetitions -> mean per seed -> overall mean/SD across seeds.
    """

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
                        "sd_execution_time_s": (
                            stdev(times) if len(times) > 1 else 0.0
                        ),
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

                # Generate each workload once for this seed/type and reuse
                # the exact request sequence for FIFO and LRU.
                workload = generator.generate(
                    network_elements=dataset_backend.network_elements,
                    workload_type=workload_type,
                    seed=seed,
                )

                for capacity in CACHE_CAPACITIES:

                    # Alternate which strategy is measured first to avoid
                    # systematically favoring one strategy through run order.
                    for repetition in range(1, REPETITIONS + 1):

                        if repetition % 2 == 1:
                            strategies = CACHE_STRATEGIES
                        else:
                            strategies = reversed(CACHE_STRATEGIES)

                        for cache_class in strategies:

                            measurement = run_timed_experiment(
                                workload=workload,
                                cache_class=cache_class,
                                capacity=capacity,
                                request_delay=request_delay,
                                timing_mode=timing_mode,
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

    # For a given mode/workload/seed/capacity/strategy, logical cache
    # results must remain identical across timing repetitions.
    logical_results = {}

    for result in results:
        key = (
            result["timing_mode"],
            result["workload_type"],
            result["seed"],
            result["capacity"],
            result["strategy"],
        )

        logical_value = (
            result["hits"],
            result["misses"],
            result["external_requests"],
        )

        if key in logical_results:
            assert logical_results[key] == logical_value
        else:
            logical_results[key] = logical_value

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
