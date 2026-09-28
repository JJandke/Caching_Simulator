import csv
from pathlib import Path

import matplotlib.pyplot as plt


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

INPUT_FILE = Path("../results/timing_summary.csv")
OUTPUT_FILE = Path("../figures/execution_time.pdf")

TIMING_MODE = "simulated_external"

WORKLOADS = [
    ("stable_locality", "Stable locality"),
    ("changing_locality", "Changing locality"),
]


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

def load_summary(path: Path) -> list[dict]:

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        raise RuntimeError(f"No data found in {path}")

    print(f"Loaded {len(rows)} rows from {path}")
    print("Columns:", list(rows[0].keys()))
    print()

    return rows


# ---------------------------------------------------------
# Extract data for one strategy
# ---------------------------------------------------------

def get_strategy_data(rows, workload, strategy):

    selected = [
        row for row in rows
        if row["timing_mode"] == TIMING_MODE
        and row["workload_type"] == workload
        and row["strategy"] == strategy
    ]

    selected.sort(
        key=lambda row: int(row["capacity"])
    )

    if not selected:
        raise RuntimeError(
            f"No rows found for "
            f"{TIMING_MODE=}, {workload=}, {strategy=}."
        )

    capacities = [
        int(row["capacity"])
        for row in selected
    ]

    # Convert seconds -> milliseconds
    means = [
        float(row["mean_execution_time_s"]) * 1000
        for row in selected
    ]

    standard_deviations = [
        float(row["sd_execution_time_s"]) * 1000
        for row in selected
    ]

    return capacities, means, standard_deviations


# ---------------------------------------------------------
# Plot one workload
# ---------------------------------------------------------

def plot_workload(ax, rows, workload, title):

    fifo_capacity, fifo_mean, fifo_sd = get_strategy_data(
        rows,
        workload,
        "FIFOCache",
    )

    lru_capacity, lru_mean, lru_sd = get_strategy_data(
        rows,
        workload,
        "LRUCache",
    )

    print(title)
    print("  FIFO [ms]:", fifo_mean)
    print("  LRU  [ms]:", lru_mean)
    print()

    # FIFO
    ax.errorbar(
        fifo_capacity,
        fifo_mean,
        yerr=fifo_sd,
        marker="o",
        markersize=5,
        linewidth=1.4,
        capsize=3,
        label="FIFO",
    )

    # LRU
    ax.errorbar(
        lru_capacity,
        lru_mean,
        yerr=lru_sd,
        marker="s",
        markersize=5,
        linewidth=1.4,
        capsize=3,
        label="LRU",
    )

    ax.set_title(title)
    ax.set_xlabel("Cache capacity")
    ax.set_xticks([3, 5, 7, 10])

    ax.grid(
        axis="y",
        linewidth=0.5,
        alpha=0.3,
    )


# ---------------------------------------------------------
# Create figure
# ---------------------------------------------------------

def create_plot(rows: list[dict]) -> None:

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(8.5, 3.4),
        sharey=True,
    )

    plot_workload(
        axes[0],
        rows,
        "stable_locality",
        "Stable locality",
    )

    plot_workload(
        axes[1],
        rows,
        "changing_locality",
        "Changing locality",
    )

    axes[0].set_ylabel("Mean execution time [ms]")

    # Use the same y-axis for both workload types
    axes[0].set_ylim(0, 600)

    # Shared legend
    handles, labels = axes[0].get_legend_handles_labels()

    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=2,
        frameon=False,
    )

    fig.tight_layout(
        rect=[0, 0.12, 1, 1]
    )

    # ---------------------------------------------------------
    # Save vector PDF
    # ---------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.savefig(
        OUTPUT_FILE,
        bbox_inches="tight",
    )

    print(f"Figure saved to: {OUTPUT_FILE}")

    plt.show()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    rows = load_summary(INPUT_FILE)
    create_plot(rows)


if __name__ == "__main__":
    main()