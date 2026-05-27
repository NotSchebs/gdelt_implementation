import pandas as pd


class TimelinePlotter:
    def __init__(self, fig, ax):
        self.fig = fig
        self.ax = ax

    def plot(self, df: pd.DataFrame, timeline_mode: str) -> None:
        self.ax.clear()

        if df is None or df.empty:
            return

        if timeline_mode in ("timelinelang", "timelinesourcecountry"):
            plot_df = df.set_index("date")
            plot_df.plot(ax=self.ax)
            title = "Timeline Breakdown by Language" if timeline_mode == "timelinelang" else "Timeline Breakdown by Source Country"
            self.ax.set_title(title, fontsize=12)
            self.ax.set_ylabel("Relative Coverage (%)", fontsize=10)
            self.ax.legend(loc="best", fontsize="small")
        else:
            value_col = "tone" if timeline_mode == "timelinetone" else "volume"
            self.ax.plot(df["date"], df[value_col], color="blue", linewidth=1.5)
            self.ax.set_title(
                "Average Tone" if timeline_mode == "timelinetone" else "Media Coverage Volume Intensity",
                fontsize=12,
            )
            self.ax.set_ylabel(
                "Average Tone" if timeline_mode == "timelinetone" else "Relative Coverage (%)",
                fontsize=10,
            )

        self.ax.set_xlabel("Date", fontsize=10)
        self.ax.grid(True, linestyle="--", alpha=0.7)
        self.fig.autofmt_xdate()
        self.fig.canvas.draw()
