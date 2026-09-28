# FIFO vs. LRU Cache Simulation

A standalone Python simulation for comparing **FIFO (First-In,
First-Out)** and **LRU (Least Recently Used)** cache replacement
strategies for software-version lookups in an agent-based network test
system.

The project was developed as the practical part of a seminar paper. It
models repeated software-version requests for network elements (NEs)
without requiring access to the production test environment. Both cache
strategies are evaluated under identical, reproducible workloads.

## Purpose

In the target test system, software versions of network elements can be
requested repeatedly while a test chain is prepared or executed.
Retrieving the same information repeatedly from an external source (for
example via SSH) creates unnecessary requests and increases processing
time.

This simulation investigates whether caching these values can reduce
external lookups and how FIFO and LRU differ with respect to:

-   **cache hit rate**
-   **number of cache misses / external requests**
-   **execution time**

The experiment intentionally isolates the caching behavior from the
production environment so that both strategies can be compared under
controlled conditions.

## Experimental Model

The simulated environment is based on the following assumptions:

  Parameter                     Value
  ----------------------------- ------------------------------------
  Available network elements    1,200
  NEs used by one workload      10
  Requests per workload         50
  Hot set                       3 NEs
  Requests targeting hot NEs    approx. 60%
  Workload types                stable locality, changing locality
  Cache capacities              3, 5, 7, 10
  Workload seeds                1--10
  Initial cache state           empty
  Timing repetitions            30
  Simulated external delay      12.39 ms
  Cache-only inner iterations   1,000

The external delay is a **1:100 scaled representation** of a measured
mean SSH request time of 1.239 s. It is an artificial delay and
therefore does not represent the exact duration of every real request.

## Architecture

The project separates the data source, cache implementations, workload
generation, logical experiment, and timing experiment.

``` mermaid
flowchart LR
    CSV["network_elements.csv"] --> Backend["SimulatedBackend"]
    Generator["WorkloadGenerator"] --> Workload["Generated Workload"]
    Workload --> Experiment["Experiment Runner"]

    Experiment --> FIFO["FIFOCache"]
    Experiment --> LRU["LRUCache"]

    FIFO --> Backend
    LRU --> Backend

    Experiment --> Results["CSV Results"]
```

At a high level, a generated workload supplies a deterministic sequence
of NE names. Each request is passed to either the FIFO or LRU cache. A
cache hit returns the stored software version directly. A cache miss
retrieves the value from `SimulatedBackend`, stores it in the cache, and
increments the external-request count.

## Project Structure

The project is organized approximately as follows:

``` text
Simulation/
├── data/
│   └── network_elements.csv
├── results/
│   ├── cache_results.csv
│   ├── cache_summary.csv
│   ├── timing_results.csv
│   └── timing_summary.csv
├── backend.py
├── caches.py
├── workload.py
├── experiment.py
├── timing_experiment.py
└── README.md
```

`backend.py` provides the simulated external data source. `caches.py`
contains the FIFO and LRU implementations and their statistics.
`workload.py` creates reproducible request sequences. `experiment.py`
evaluates logical cache behavior, while `timing_experiment.py` performs
repeated execution-time measurements.

## Main Components

### `SimulatedBackend`

`SimulatedBackend` represents the external source from which a software
version would normally be retrieved.

The CSV dataset is loaded into memory so that normal cache experiments
are not influenced by repeated file-system access. The backend
additionally counts external requests and can introduce a controlled
artificial delay for timing experiments.

Conceptually:

``` text
NE name
   │
   ▼
SimulatedBackend
   │
   ├── look up software version
   ├── increment request counter
   └── optionally wait for simulated external delay
```

### FIFO Cache

FIFO evicts the entry that has been in the cache for the longest time. A
cache hit does **not** change the order of entries.

``` mermaid
flowchart LR
    A["Oldest entry"] --> B["Entry"]
    B --> C["Newest entry"]
    D["New entry"] --> C
    A -. "evicted when full" .-> X["removed"]
```

For a cache hit, the implementation only increments the hit counter and
returns the cached value.

### LRU Cache

LRU evicts the entry that has gone unused for the longest time.
Therefore, a cache hit also updates the entry's recency.

``` mermaid
flowchart LR
    A["Least recently used"] --> B["Entry"]
    B --> C["Most recently used"]
    A -. "evicted when full" .-> X["removed"]
    H["Cache hit"] -. "move to most-recent position" .-> C
```

This behavioral difference is central to the comparison: FIFO uses
**insertion order**, whereas LRU also reacts to subsequent accesses.

## Simplified Class Structure

GitHub renders Mermaid diagrams directly in Markdown. The following
diagram documents the logical relationships between the principal
components.

``` mermaid
classDiagram
    class SimulatedBackend {
        +network_elements
        +request_count
        +get(...)
    }

    class FIFOCache {
        +capacity
        +statistics
        +get(ne_name)
    }

    class LRUCache {
        +capacity
        +statistics
        +get(ne_name)
    }

    class CacheStatistics {
        +hits
        +misses
    }

    class WorkloadGenerator {
        +generate(network_elements, workload_type, seed)
    }

    class Workload {
        +requests
        +hot_sets
    }

    class WorkloadType {
        <<enumeration>>
        STABLE_LOCALITY
        CHANGING_LOCALITY
    }

    FIFOCache --> SimulatedBackend : requests misses
    LRUCache --> SimulatedBackend : requests misses
    FIFOCache --> CacheStatistics
    LRUCache --> CacheStatistics
    WorkloadGenerator --> Workload : creates
    WorkloadGenerator --> WorkloadType : uses
```

The diagram is intentionally conceptual; implementation details that are
not relevant to understanding the experiment are omitted.

## Workload Generation

Workloads are generated deterministically using seeds. This makes it
possible to run FIFO and LRU against the **same request sequence**,
which is necessary for a meaningful comparison.

Each workload contains 50 requests to a working set of 10 network
elements. The first accesses initialize the working set, after which the
generated requests model locality.

### Stable Locality

A fixed hot set of three NEs receives a disproportionately large share
of subsequent requests.

``` mermaid
flowchart LR
    Start["Start workload"] --> Init["Initial NE accesses"]
    Init --> Phase["Remaining requests"]
    Phase --> Hot["~60%: fixed hot set"]
    Phase --> Other["~40%: other NEs"]
```

This models a test in which a small subset of devices is queried
repeatedly throughout the test.

### Changing Locality

The frequently accessed subset changes during the workload.

``` mermaid
flowchart LR
    Start["Start workload"] --> Init["Initial NE accesses"]
    Init --> P1["Phase 1"]
    P1 --> H1["Hot set A"]
    H1 --> P2["Phase 2"]
    P2 --> H2["Hot set B"]
```

This represents situations in which different network elements become
relevant during different phases of a test, for example after
configuration changes.

## Logical Cache Experiment

`experiment.py` compares the cache behavior independently of
execution-time noise.

For every combination of:

-   workload type,
-   seed,
-   cache capacity, and
-   cache strategy,

the complete request sequence is executed with an initially empty cache.

The experiment records:

-   hits,
-   misses,
-   hit rate, and
-   external requests.

Because every miss requires access to the backend:

``` text
external requests = cache misses
```

The raw observations are written to:

``` text
results/cache_results.csv
```

Aggregated results are written to:

``` text
results/cache_summary.csv
```

The raw file preserves individual seed results, while the summary file
provides the values required for comparison.

## Timing Experiment

`timing_experiment.py` measures execution time separately from the
logical experiment. Two timing modes are used.

### Simulated External Requests

`simulated_external` introduces an artificial delay of **12.39 ms for
each external request**.

This mode represents the practical effect of cache misses on total
processing time. A strategy that avoids an external request can
therefore also avoid its simulated retrieval delay.

Each configuration is measured repeatedly using `time.perf_counter()`.

### Cache-Only Timing

`cache_only` uses no artificial external delay and is intended to
examine the overhead of the cache algorithms themselves.

Because a complete 50-request workload takes only a few microseconds,
timing a single execution would be highly susceptible to timer and
operating-system noise. Each timing measurement therefore executes the
complete workload **1,000 times** and reports the average time per
workload.

A fresh cache is created for every inner execution, while the backend is
initialized outside the timed section. This prevents CSV loading from
becoming part of the cache benchmark.

### Measurement Order

FIFO and LRU are interleaved during timing measurements. The strategy
executed first is alternated between repetitions:

``` text
Repetition 1: FIFO → LRU
Repetition 2: LRU  → FIFO
Repetition 3: FIFO → LRU
...
```

This reduces systematic bias caused by always measuring one strategy
before the other.

### Timing Aggregation

Timing results are aggregated in two stages:

``` mermaid
flowchart LR
    R["30 timing repetitions"] --> S["Mean for one seed"]
    S --> M["10 seed means"]
    M --> F["Overall mean and standard deviation"]
```

Repeated measurements of the same workload are therefore not treated as
30 independent workloads.

Raw timing observations are stored in:

``` text
results/timing_results.csv
```

and aggregated timing data in:

``` text
results/timing_summary.csv
```

## Reproducibility

The workload generator uses explicit random seeds. Consequently, the
same seed and workload type produce the same request sequence for FIFO
and LRU.

This is important because differences in the result should arise from
the cache replacement strategy rather than from different request
sequences.

For the final experiment, the intended configuration is:

``` python
SEEDS = range(1, 11)
CACHE_CAPACITIES = [3, 5, 7, 10]
REPETITIONS = 30
CACHE_ONLY_INNER_ITERATIONS = 1000
```

The timing experiment therefore contains:

``` text
2 timing modes
× 2 workload types
× 10 seeds
× 4 cache capacities
× 2 strategies
× 30 repetitions
= 9,600 timed measurements
```

The cache-only mode additionally performs 1,000 inner workload
executions per timing observation.

## Running the Project

A recent Python 3 installation is required. The current implementation
relies primarily on the Python standard library.

Run the logical cache experiment with:

``` bash
python experiment.py
```

Run the execution-time experiment with:

``` bash
python timing_experiment.py
```

Both scripts write their generated CSV files to the `results/`
directory.

Before running the final timing experiment, verify that the
development/test values in `timing_experiment.py` have been replaced
with the final configuration.

## Result Interpretation

The experiment is designed to distinguish three related but different
effects:

1.  **Cache hit rate** describes how often a requested software version
    can be returned from the cache.
2.  **External requests** describe the practical consequence of misses,
    because every miss requires a backend lookup.
3.  **Execution time** tests whether differences in cache behavior also
    translate into measurable processing-time differences.

The cache-only benchmark should be interpreted cautiously. FIFO/LRU
processing for only 50 requests is extremely fast, so very small
differences can be affected by Python runtime behavior and
operating-system scheduling. The simulated-external mode is more
representative of the practical consequence of avoiding expensive
external lookups.

## Experimental Limitations

This project is a controlled simulation rather than a production
implementation. In particular:

-   software-version retrieval is represented by an in-memory backend
    rather than a real agent or network connection;
-   the external-request duration is modeled using a scaled artificial
    delay;
-   workloads approximate observed test-system behavior but do not
    reproduce every possible production access pattern;
-   only FIFO and LRU are compared;
-   cache capacities and workload sizes are deliberately limited to the
    investigated scenarios;
-   concurrency, network failures, changing software versions, cache
    invalidation, and distributed caches are outside the current
    experiment.

These restrictions make the experiment reproducible and isolate the
cache replacement strategies, but the results should not be interpreted
as direct production performance measurements.

## Data Files

`data/network_elements.csv` serves as the simulated database. It
contains network-element names and corresponding software versions used
by `SimulatedBackend`.

The dataset is static during an experiment. This ensures that FIFO and
LRU operate on identical source data and that cache invalidation is not
a factor in the comparison.

## Development Notes

When modifying the project, keep the following experimental properties
intact:

-   FIFO and LRU must receive identical workloads.
-   Every run must start with an empty cache.
-   Workload generation must remain reproducible through seeds.
-   Dataset loading must not be included in cache-only timing.
-   Logical cache results must not change between timing repetitions.
-   Raw result files should be retained so aggregated values remain
    traceable.
-   Experimental parameters should not be changed after inspecting final
    results unless the experiment is explicitly repeated and documented
    as a new configuration.

## License and Internal Context

No license is specified by this project documentation.

The simulation was developed for an academic comparison of cache
replacement strategies in the context of software-version lookups in an
agent-based network test environment. It does not itself connect to or
modify production network elements.
