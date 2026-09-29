import csv
from pathlib import Path

import matplotlib.pyplot as plt


INPUT_FILE = Path("../results/cache_summary.csv")
OUTPUT_FILE = Path("../figures/cache_hit_rate.pdf")


def load_summary(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        raise RuntimeError(f"No data found in {path}")

    print(f"Loaded {len(rows)} rows from {path}")
    print("Columns:", list(rows[0].keys()))
    print()

    for row in rows:
        # Remove accidental whitespace
        row["workload_type"] = row["workload_type"].strip()

        row["capacity"] = int(row["capacity"])

        row["fifo_mean_hit_rate"] = float(row["fifo_mean_hit_rate"])
        row["fifo_sd_hit_rate"] = float(row["fifo_sd_hit_rate"])

        row["lru_mean_hit_rate"] = float(row["lru_mean_hit_rate"])
        row["lru_sd_hit_rate"] = float(row["lru_sd_hit_rate"])

    print("Workloads found:")
    for workload in sorted(set(row["workload_type"] for row in rows)):
        print(f"  {workload!r}")

    print()

    return rows


def plot_workload(ax, rows, workload, title):
    workload_rows = [
        row
        for row in rows
        if row["workload_type"] == workload
    ]

    workload_rows.sort(
        key=lambda row: row["capacity"]
    )

    if not workload_rows:
        raise RuntimeError(
            f"No rows found for workload {workload!r}. "
            "Check the workload names printed above."
        )

    capacities = [
        row["capacity"]
        for row in workload_rows
    ]

    fifo_mean = [
        row["fifo_mean_hit_rate"] * 100
        for row in workload_rows
    ]

    fifo_sd = [
        row["fifo_sd_hit_rate"] * 100
        for row in workload_rows
    ]

    lru_mean = [
        row["lru_mean_hit_rate"] * 100
        for row in workload_rows
    ]

    lru_sd = [
        row["lru_sd_hit_rate"] * 100
        for row in workload_rows
    ]

    print(title)
    print("  Capacities:", capacities)
    print("  FIFO mean:", fifo_mean)
    print("  LRU mean: ", lru_mean)
    print()

    ax.errorbar(
        capacities,
        fifo_mean,
        yerr=fifo_sd,
        marker="o",
        markersize=5,
        linewidth=1.4,
        capsize=3,
        label="FIFO",
    )

    ax.errorbar(
        capacities,
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

    ax.set_ylim(20, 90)
    ax.set_yticks(range(20, 91, 10))

    ax.grid(
        axis="y",
        linewidth=0.5,
        alpha=0.3,
    )


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
        "Temporal locality",
    )

    axes[0].set_ylabel("Mean cache hit rate [%]")

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


def main():
    rows = load_summary(INPUT_FILE)
    create_plot(rows)


if __name__ == "__main__":
    main()