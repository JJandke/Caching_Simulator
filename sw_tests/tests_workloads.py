from collections import Counter

from backend import SimulatedBackend
from workload import WorkloadGenerator, WorkloadType


backend = SimulatedBackend(
    "../data/network_elements.csv",
    request_delay=0,
)

generator = WorkloadGenerator()

stable = generator.generate(
    backend.network_elements,
    WorkloadType.STABLE_LOCALITY,
    seed=1,
)

hot_set = set(stable.hot_sets[0])

hot_requests = sum(
    1
    for ne in stable.requests
    if ne in hot_set
)

print(hot_requests)


for workload_type in WorkloadType:

    workload = generator.generate(
        network_elements=backend.network_elements,
        workload_type=workload_type,
        seed=1,
    )

    print()
    print("=" * 60)
    print(workload_type.value)
    print("=" * 60)

    print("Seed:")
    print(workload.seed)

    print("\nWorking set:")
    print(workload.working_set)

    print("\nHot sets:")
    print(workload.hot_sets)

    print("\nRequests:")
    print(workload.requests)

    print("\nRequest counts:")
    print(Counter(workload.requests))