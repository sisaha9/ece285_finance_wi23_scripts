import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from settings import RESULTS_DIR, Y_OFFSET, XROT, FIGSIZE, BBOX_ANCHOR


def generate_valuations_barplot(plot_df: pd.DataFrame, file_name="valuations"):
    fig = plot_df.set_index("Labels").plot(
        kind="bar",
        stacked=True,
        xlabel="Time",
        ylabel="Portfolio value in USD",
        title="Valuations of Portfolio",
        rot=XROT,
        figsize=FIGSIZE,
    )
    plt.legend(loc="upper left", bbox_to_anchor=BBOX_ANCHOR)
    for label, total_price in (
        plot_df.set_index("Labels").sum(axis=1).reset_index(drop=True).items()
    ):
        fig.text(label, total_price + Y_OFFSET, round(total_price), ha="center", weight="bold")
    for bar in fig.patches:
        fig.text(
            bar.get_x() + (bar.get_width() / 2),
            bar.get_y() + (bar.get_height() / 2),
            round(bar.get_height()),
            ha="center",
            color="w",
            weight="bold",
        )
    if RESULTS_DIR:
        plt.savefig(Path(RESULTS_DIR) / f"{file_name}.png", bbox_inches="tight")
        print("Plot generated")
    plt.show()
