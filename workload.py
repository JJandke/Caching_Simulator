import random
from dataclasses import dataclass
from enum import Enum


class WorkloadType(Enum):
    STABLE_LOCALITY = "stable_locality"
    CHANGING_LOCALITY = "changing_locality"


@dataclass
class Workload:
    requests: list[str]
    working_set: list[str]
    workload_type: WorkloadType
    seed: int
    hot_sets: list[list[str]]


class WorkloadGenerator:
    """
    Generates reproducible request sequences for the cache experiment.

    Common workload structure:
        - 10 network elements per working set
        - 50 requests in total
        - first 10 requests initialize the workload by requesting
          every NE exactly once

    Stable locality:
        - one hot set containing 3 NEs
        - hot NEs account for 60% of all 50 requests

    Changing locality:
        - two phases after initialization
        - each phase contains 20 requests
        - each phase has a different hot set containing 3 NEs
        - the current hot set accounts for 60% of requests
          within its phase
    """

    WORKING_SET_SIZE = 10
    TOTAL_REQUESTS = 50
    HOT_SET_SIZE = 3

    def generate(
        self,
        network_elements: list[str],
        workload_type: WorkloadType,
        seed: int,
    ) -> Workload:

        if len(network_elements) < self.WORKING_SET_SIZE:
            raise ValueError(
                f"At least {self.WORKING_SET_SIZE} network elements "
                "are required."
            )

        rng = random.Random(seed)

        # Select 10 NEs from the complete dataset.
        working_set = rng.sample(
            network_elements,
            self.WORKING_SET_SIZE,
        )

        # Every workload starts by requesting every NE exactly once.
        initialization = working_set.copy()

        if workload_type == WorkloadType.STABLE_LOCALITY:
            requests, hot_sets = self._generate_stable(
                working_set,
                initialization,
                rng,
            )

        elif workload_type == WorkloadType.CHANGING_LOCALITY:
            requests, hot_sets = self._generate_changing(
                working_set,
                initialization,
                rng,
            )

        else:
            raise ValueError(
                f"Unsupported workload type: {workload_type}"
            )

        workload = Workload(
            requests=requests,
            working_set=working_set,
            workload_type=workload_type,
            seed=seed,
            hot_sets=hot_sets,
        )

        self._validate(workload)

        return workload

    def _generate_stable(
        self,
        working_set: list[str],
        initialization: list[str],
        rng: random.Random,
    ) -> tuple[list[str], list[list[str]]]:

        hot_set = rng.sample(
            working_set,
            self.HOT_SET_SIZE,
        )

        cold_set = [
            ne for ne in working_set
            if ne not in hot_set
        ]

        # 60% of all 50 requests = 30 hot requests.
        #
        # Each hot NE already occurs once during initialization,
        # resulting in 3 existing hot requests.
        #
        # Therefore:
        #     30 - 3 = 27 additional hot requests
        #
        # The remaining:
        #     40 - 27 = 13
        #
        # requests go to the cold set.

        hot_requests = [
            rng.choice(hot_set)
            for _ in range(27)
        ]

        cold_requests = [
            rng.choice(cold_set)
            for _ in range(13)
        ]

        remaining_requests = (
            hot_requests + cold_requests
        )

        rng.shuffle(remaining_requests)

        requests = (
            initialization
            + remaining_requests
        )

        return requests, [hot_set]

    def _generate_changing(
        self,
        working_set: list[str],
        initialization: list[str],
        rng: random.Random,
    ) -> tuple[list[str], list[list[str]]]:

        # Select two non-overlapping hot sets.
        selected_hot_elements = rng.sample(
            working_set,
            self.HOT_SET_SIZE * 2,
        )

        first_hot_set = selected_hot_elements[
            :self.HOT_SET_SIZE
        ]

        second_hot_set = selected_hot_elements[
            self.HOT_SET_SIZE:
        ]

        phase_1 = self._generate_phase(
            working_set,
            first_hot_set,
            rng,
        )

        phase_2 = self._generate_phase(
            working_set,
            second_hot_set,
            rng,
        )

        requests = (
            initialization
            + phase_1
            + phase_2
        )

        return requests, [
            first_hot_set,
            second_hot_set,
        ]

    @staticmethod
    def _generate_phase(
        working_set: list[str],
        hot_set: list[str],
        rng: random.Random,
    ) -> list[str]:

        cold_set = [
            ne for ne in working_set
            if ne not in hot_set
        ]

        # Each phase contains 20 requests:
        #
        #     12 hot  = 60%
        #      8 cold = 40%

        hot_requests = [
            rng.choice(hot_set)
            for _ in range(12)
        ]

        cold_requests = [
            rng.choice(cold_set)
            for _ in range(8)
        ]

        phase = hot_requests + cold_requests

        rng.shuffle(phase)

        return phase

    def _validate(
        self,
        workload: Workload,
    ) -> None:

        if len(workload.requests) != self.TOTAL_REQUESTS:
            raise ValueError(
                "Generated workload does not contain "
                f"{self.TOTAL_REQUESTS} requests."
            )

        if len(workload.working_set) != self.WORKING_SET_SIZE:
            raise ValueError(
                "Generated working set does not contain "
                f"{self.WORKING_SET_SIZE} NEs."
            )

        if len(set(workload.working_set)) != self.WORKING_SET_SIZE:
            raise ValueError(
                "Working set contains duplicate NEs."
            )

        # Verify initialization phase.
        initialization = workload.requests[
            :self.WORKING_SET_SIZE
        ]

        if initialization != workload.working_set:
            raise ValueError(
                "Initialization phase is invalid."
            )

        # Every request must belong to the working set.
        if not all(
            ne in workload.working_set
            for ne in workload.requests
        ):
            raise ValueError(
                "Workload contains an NE outside its working set."
            )

        # Verify stable locality
        if workload.workload_type == WorkloadType.STABLE_LOCALITY:
            hot_set = set(workload.hot_sets[0])

            hot_requests = sum(
                ne in hot_set
                for ne in workload.requests
            )

            if hot_requests != 30:
                raise ValueError(
                    f"Stable workload must contain exactly 30 hot requests, "
                    f"but contains {hot_requests}."
                )

        # Verify changing locality
        if workload.workload_type == WorkloadType.CHANGING_LOCALITY:
            phase_1 = workload.requests[10:30]
            phase_2 = workload.requests[30:50]

            hot_set_1 = set(workload.hot_sets[0])
            hot_set_2 = set(workload.hot_sets[1])

            phase_1_hot = sum(
                ne in hot_set_1
                for ne in phase_1
            )

            phase_2_hot = sum(
                ne in hot_set_2
                for ne in phase_2
            )

            if phase_1_hot != 12 or phase_2_hot != 12:
                raise ValueError(
                    "Changing-locality workload must contain exactly "
                    "12 hot requests in each phase."
                )