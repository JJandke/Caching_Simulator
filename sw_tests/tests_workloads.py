from collections import Counter

from backend import SimulatedBackend
from workload import WorkloadGenerator, WorkloadType


backend = SimulatedBackend(
    "data/network_elements.csv",
    request_delay=0,
)

generator = WorkloadGenerator()


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