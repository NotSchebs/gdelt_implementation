import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import warnings

warnings.filterwarnings('ignore')


class DashboardApp:
    def __init__(self, root, timeline_data, articles_data=None, keyword=""):
        self.root = root
        self.root.title(f"GDELT Analysis Dashboard - {keyword}")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.timeline_df = timeline_data.copy()
        self.articles_df = articles_data.copy() if articles_data is not None else None
        self.keyword = keyword

        self.forecast_df = None
        self.arima_model = None
        self.arima_order = (1, 1, 1)

        self._create_ui()

    def _create_ui(self):
        # Control Panel
        control_frame = tk.Frame(self.root, padx=10, pady=10, bg="lightgray")
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # ############# Uncomment for analysis controls
        tk.Label(control_frame, text="ARIMA Order (p,d,q):", bg="lightgray").pack(side=tk.LEFT, padx=5)

        self.p_var = tk.StringVar(value="1")
        self.d_var = tk.StringVar(value="1")
        self.q_var = tk.StringVar(value="1")

        tk.Label(control_frame, text="p:", bg="lightgray").pack(side=tk.LEFT, padx=2)
        tk.Entry(control_frame, textvariable=self.p_var, width=3).pack(side=tk.LEFT, padx=2)

        tk.Label(control_frame, text="d:", bg="lightgray").pack(side=tk.LEFT, padx=2)
        tk.Entry(control_frame, textvariable=self.d_var, width=3).pack(side=tk.LEFT, padx=2)

        tk.Label(control_frame, text="q:", bg="lightgray").pack(side=tk.LEFT, padx=2)
        tk.Entry(control_frame, textvariable=self.q_var, width=3).pack(side=tk.LEFT, padx=2)

        tk.Label(control_frame, text="Forecast steps:", bg="lightgray").pack(side=tk.LEFT, padx=5)
        self.forecast_steps_var = tk.StringVar(value="10")
        tk.Entry(control_frame, textvariable=self.forecast_steps_var, width=5).pack(side=tk.LEFT, padx=2)

        tk.Button(control_frame, text="Run ARIMA", command=self.run_arima, bg="green", fg="white").pack(
            side=tk.LEFT, padx=5
        )

        tk.Button(control_frame, text="Export Forecast", command=self.export_forecast, bg="blue", fg="white").pack(
            side=tk.LEFT, padx=5
        )
        # ############# End analysis controls

        tk.Button(control_frame, text="Back to Search", command=self.close_app).pack(side=tk.LEFT, padx=5)

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Tab 1: Timeline Plot
        self.timeline_frame = tk.Frame(self.notebook)
        self.notebook.add(self.timeline_frame, text="Timeline")

        self.fig_timeline, self.ax_timeline = plt.subplots(figsize=(10, 4))
        self.canvas_timeline = FigureCanvasTkAgg(self.fig_timeline, master=self.timeline_frame)
        self.canvas_timeline.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ############# Analysis tabs - uncomment for forecast/diagnostics
        # Tab 2: Forecast Plot
        self.forecast_frame = tk.Frame(self.notebook)
        self.notebook.add(self.forecast_frame, text="Forecast")

        self.fig_forecast, self.ax_forecast = plt.subplots(figsize=(10, 4))
        self.canvas_forecast = FigureCanvasTkAgg(self.fig_forecast, master=self.forecast_frame)
        self.canvas_forecast.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab 3: Diagnostics (ACF/PACF)
        self.diagnostics_frame = tk.Frame(self.notebook)
        self.notebook.add(self.diagnostics_frame, text="Diagnostics")

        self.fig_diag, ((self.ax_acf, self.ax_pacf), (self.ax_res, self.ax_res2)) = plt.subplots(2, 2, figsize=(10, 8))
        self.canvas_diag = FigureCanvasTkAgg(self.fig_diag, master=self.diagnostics_frame)
        self.canvas_diag.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Status Log
        log_frame = tk.Frame(self.root)
        log_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        tk.Label(log_frame, text="Status Log:").pack(side=tk.TOP, anchor=tk.W)
        self.log_text = tk.Text(log_frame, height=4, state=tk.DISABLED)
        self.log_text.pack(side=tk.TOP, fill=tk.X)

        # Draw initial timeline
        self._plot_timeline()
        self.root.bind("<Configure>", self._schedule_resize)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _schedule_resize(self, event):
        if getattr(self, "_resize_after_id", None):
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(100, self._resize_figures)

    def _resize_figures(self):
        for fig, canvas in [
            (self.fig_timeline, self.canvas_timeline),
            (self.fig_forecast, self.canvas_forecast),
            (self.fig_diag, self.canvas_diag),
        ]:
            widget = canvas.get_tk_widget()
            width = widget.winfo_width()
            height = widget.winfo_height()
            if width > 20 and height > 20:
                dpi = fig.get_dpi()
                fig.set_size_inches(width / dpi, height / dpi)
                fig.tight_layout()
                canvas.draw()

    def _plot_timeline(self):
        self.ax_timeline.clear()

        if self.timeline_df is not None and not self.timeline_df.empty:
            self.ax_timeline.plot(self.timeline_df["date"], self.timeline_df["volume"], color="blue", linewidth=1.5)

            if "n_articles" in self.timeline_df.columns:
                ax2 = self.ax_timeline.twinx()
                ax2.bar(
                    self.timeline_df["date"],
                    self.timeline_df["n_articles"],
                    color="red",
                    alpha=0.3,
                    label="Article Count",
                )
                ax2.set_ylabel("Article Count", color="red")
                ax2.tick_params(axis="y", labelcolor="red")

            self.ax_timeline.set_title("Timeline Data")
            self.ax_timeline.set_xlabel("Date")
            self.ax_timeline.set_ylabel("Volume Intensity")
            self.ax_timeline.grid(True, linestyle="--", alpha=0.7)
            self.fig_timeline.autofmt_xdate()
            self.canvas_timeline.draw()
            self.log("Timeline plot displayed.")

    # ############# Analysis functions - uncomment for ARIMA modeling and diagnostics
    def run_arima(self):
        try:
            p = int(self.p_var.get())
            d = int(self.d_var.get())
            q = int(self.q_var.get())
            steps = int(self.forecast_steps_var.get())

            self.arima_order = (p, d, q)

            self.log(f"Fitting ARIMA{self.arima_order}...")

            volume_data = self.timeline_df["volume"].values
            self.arima_model = ARIMA(volume_data, order=self.arima_order)
            results = self.arima_model.fit()

            self.log(f"ARIMA fit complete. AIC: {results.aic:.2f}")

            # Forecast
            forecast = results.get_forecast(steps=steps)
            forecast_df = forecast.summary_frame()

            self.forecast_df = forecast_df.copy()

            # Plot forecast
            self._plot_forecast(volume_data, forecast_df)

            # Plot diagnostics
            self._plot_diagnostics(results)

            self.log("Forecast and diagnostics plotted.")

        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid ARIMA parameters: {str(e)}")
        except Exception as e:
            messagebox.showerror("ARIMA Error", f"Failed to fit ARIMA: {str(e)}")

    def _plot_forecast(self, history, forecast_df):
        self.ax_forecast.clear()

        dates = np.arange(len(history))
        self.ax_forecast.plot(dates, history, label="Historical", color="blue", linewidth=1.5)

        forecast_dates = np.arange(len(history), len(history) + len(forecast_df))
        self.ax_forecast.plot(forecast_dates, forecast_df["mean"], label="Forecast", color="red", linewidth=1.5)

        self.ax_forecast.fill_between(
            forecast_dates,
            forecast_df["mean_ci_lower"],
            forecast_df["mean_ci_upper"],
            color="red",
            alpha=0.2,
            label="95% CI",
        )

        self.ax_forecast.set_title(f"ARIMA{self.arima_order} Forecast")
        self.ax_forecast.set_xlabel("Time Steps")
        self.ax_forecast.set_ylabel("Volume Intensity")
        self.ax_forecast.legend()
        self.ax_forecast.grid(True, linestyle="--", alpha=0.7)
        self.fig_forecast.tight_layout()
        self.canvas_forecast.draw()

    def _plot_diagnostics(self, results):
        self.ax_acf.clear()
        self.ax_pacf.clear()
        self.ax_res.clear()
        self.ax_res2.clear()

        plot_acf(results.resid, lags=20, ax=self.ax_acf)
        plot_pacf(results.resid, lags=20, ax=self.ax_pacf)

        self.ax_res.plot(results.resid)
        self.ax_res.set_title("Residuals")
        self.ax_res.grid(True, linestyle="--", alpha=0.7)

        self.ax_res2.hist(results.resid, bins=20, edgecolor="black")
        self.ax_res2.set_title("Residuals Distribution")

        self.fig_diag.tight_layout()
        self.canvas_diag.draw()

    def export_forecast(self):
        if self.forecast_df is None:
            messagebox.showwarning("Export Error", "No forecast data to export. Run ARIMA first.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"arima_forecast_{self.keyword}.csv",
            title="Save Forecast",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )

        if filepath:
            try:
                self.forecast_df.to_csv(filepath)
                self.log(f"Forecast exported to {filepath}")
                messagebox.showinfo("Export Success", f"Forecast saved to {filepath}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def close_app(self):
        self.root.quit()


def launch_dashboard(timeline_csv_path, articles_csv_path=None, keyword=""):
    """
    Load CSV files and launch the dashboard.
    
    Parameters:
    - timeline_csv_path: path to timeline CSV
    - articles_csv_path: optional path to articles CSV
    - keyword: keyword string for the window title
    """
    try:
        timeline_df = pd.read_csv(timeline_csv_path)
        articles_df = pd.read_csv(articles_csv_path) if articles_csv_path and os.path.exists(articles_csv_path) else None

        root = tk.Tk()
        app = DashboardApp(root, timeline_df, articles_df, keyword)
        root.mainloop()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load data: {str(e)}")


if __name__ == "__main__":
    # For testing only
    root = tk.Tk()
    sample_data = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=100),
        "volume": np.random.rand(100) * 100,
        "n_articles": np.random.randint(0, 50, 100)
    })
    app = DashboardApp(root, sample_data, None, "test")
    root.mainloop()
