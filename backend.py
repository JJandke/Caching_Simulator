import csv
import time
from pathlib import Path


class SimulatedBackend:
    """
    Simulates the external source used to retrieve software versions.

    The CSV dataset is loaded into memory once during initialization.
    Every fetch() call represents one external request and therefore
    includes the configured artificial delay.
    """

    def __init__(
        self,
        csv_path: str | Path,
        request_delay: float = 0.01239,
    ) -> None:
        self.request_delay = request_delay
        self._versions = self._load_dataset(csv_path)
        self.request_count = 0

    @staticmethod
    def _load_dataset(csv_path: str | Path) -> dict[str, str]:
        versions: dict[str, str] = {}

        with open(csv_path, "r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            required_columns = {"ne_name", "software_version"}

            if reader.fieldnames is None:
                raise ValueError("CSV file does not contain a header.")

            if not required_columns.issubset(reader.fieldnames):
                raise ValueError(
                    "CSV file must contain the columns "
                    "'ne_name' and 'software_version'."
                )

            for row in reader:
                ne_name = row["ne_name"].strip()
                software_version = row["software_version"].strip()

                if not ne_name:
                    continue

                if ne_name in versions:
                    raise ValueError(
                        f"Duplicate network element in dataset: {ne_name}"
                    )

                versions[ne_name] = software_version

        return versions

    def fetch(self, ne_name: str) -> str:
        """
        Retrieve a software version from the simulated external source.
        """

        if ne_name not in self._versions:
            raise KeyError(f"Unknown network element: {ne_name}")

        self.request_count += 1

        time.sleep(self.request_delay)

        return self._versions[ne_name]

    def reset_statistics(self) -> None:
        self.request_count = 0

    @property
    def size(self) -> int:
        return len(self._versions)