import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gdeltdoc import GdeltDoc, Filters
from gdeltdoc.errors import RateLimitError
from datetime import datetime, timedelta
import threading
import time

class GdeltApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GDELT Trend Analysis Tool")
        self.root.geometry("1000x700")

        self.df = None  # To store the current fetched data
        self.stop_event = threading.Event()
        self.is_fetching = False
        self._create_ui()

    def _create_ui(self):
        # Top Frame for Controls
        control_frame = tk.Frame(self.root, padx=10, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # Keyword
        tk.Label(
            control_frame,
            text="Keyword:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 5),
            pady=5
        )

        self.keyword_entry = tk.Entry(
            control_frame,
            width=25
        )

        self.keyword_entry.grid(
            row=0,
            column=0,
            sticky="e",
            padx=(0, 10),
            pady=5
        )

        self.keyword_entry.insert(0, "quantum computing")

         #articles box
        tk.Label(control_frame, text="Articles (keep in mind max 250 articles can be fetched):").grid(row=1, column=0, sticky =tk.W, pady = 5)

        # Time Span
        tk.Label(
            control_frame,
            text="Time Span:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 5),
            pady=5
        )

        self.time_span_var = tk.StringVar(value="Last Month")

        time_spans = [
            "Last Week",
            "Last Month",
            "2020 - Yesterday",
            "Custom"
        ]

        self.time_span_menu = ttk.Combobox(
            control_frame,
            textvariable=self.time_span_var,
            values=time_spans,
            state="readonly",
            width=15
        )

        self.time_span_menu.grid(
            row=2,
            column=0,
            sticky="e",
            padx=(0, 10),
            pady=5
        )

        self.time_span_menu.bind(
            "<<ComboboxSelected>>",
            self._on_time_span_change
        )

        # Custom Dates (Initially disabled)
        self.date_frame = tk.Frame(control_frame)
        self.date_frame.grid(row=3, column=0)
        
        tk.Label(self.date_frame, text="Start (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.start_date_entry = tk.Entry(self.date_frame, width=12)
        self.start_date_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.date_frame, text="End (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.end_date_entry = tk.Entry(self.date_frame, width=12)
        self.end_date_entry.pack(side=tk.LEFT, padx=5)

        self._update_date_entries_state()

        # Buttons
        btn_frame = tk.Frame(control_frame)
        btn_frame.grid(row=0, column=2, rowspan=1, padx=10)

        self.search_btn = tk.Button(btn_frame, text="Search", command=self.start_search, width=10, bg="green")
        self.search_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(btn_frame, text="Stop", command=self.stop_search, width=10, state=tk.DISABLED, bg="red")
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.export_btn = tk.Button(btn_frame, text="Export CSV", command=self.export_csv, width=10, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=5)

        # Plot Area
        self.plot_frame = tk.Frame(self.root, bg="white", bd=2, relief=tk.SUNKEN)
        self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Log Area
        log_frame = tk.Frame(self.root)
        log_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        tk.Label(log_frame, text="Status Log:").pack(side=tk.TOP, anchor=tk.W)
        self.log_text = tk.Text(log_frame, height=6, state=tk.DISABLED)
        self.log_text.pack(side=tk.TOP, fill=tk.X)

    def _on_time_span_change(self, event=None):
        self._update_date_entries_state()

    def _update_date_entries_state(self):
        if self.time_span_var.get() == "Custom":
            self.start_date_entry.config(state=tk.NORMAL)
            self.end_date_entry.config(state=tk.NORMAL)
        else:
            self.start_date_entry.config(state=tk.DISABLED)
            self.end_date_entry.config(state=tk.DISABLED)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{time_str}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _get_date_range(self):
        span = self.time_span_var.get()
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        if span == "Last Week":
            start = yesterday - timedelta(days=7)
            end = yesterday
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        elif span == "Last Month":
            start = yesterday - timedelta(days=30)
            end = yesterday
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        elif span == "2020 - Yesterday":
            return "2020-01-01", yesterday.strftime("%Y-%m-%d")
        else:
            return self.start_date_entry.get(), self.end_date_entry.get()

    def start_search(self):
        keyword = self.keyword_entry.get().strip()
        start_date, end_date = self._get_date_range()

        if not keyword:
            messagebox.showerror("Input Error", "Please enter a keyword.")
            return

        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        self.log(f"Starting search for '{keyword}' from {start_date} to {end_date}...")
        
        self.search_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.DISABLED)
        self.stop_event.clear()
        self.is_fetching = True
        self.df = None
        self.ax.clear()
        self.canvas.draw()

        # Run in a background thread
        threading.Thread(target=self._fetch_data, args=(keyword, start_date, end_date), daemon=True).start()

    def stop_search(self):
        self.log("Stopping search requested...")
        self.stop_event.set()

    def _fetch_data(self, keyword, start_date, end_date):
        gd = GdeltDoc()
        f = Filters(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date
        )

        try:
            if self.stop_event.is_set():
                self._on_search_finished(success=False, msg="Search stopped by user.")
                return

            self.log("Calling GDELT API (this may take a while)...")
            timeline = gd.timeline_search("timelinevol", f)

            if self.stop_event.is_set():
                self._on_search_finished(success=False, msg="Search stopped by user.")
                return

            self.log("API Call successful. Processing data...")
            df = pd.DataFrame(timeline)
            
            if df.empty:
                self._on_search_finished(success=False, msg="No data found for this query.")
                return

            # Clean and group by day as done in the notebook
            df['datetime'] = pd.to_datetime(df['datetime'])
            df['date'] = df['datetime'].dt.date
            daily = df.groupby("date")["Volume Intensity"].mean().reset_index()
            daily.columns = ["date", "volume"]

            self.df = daily
            self._on_search_finished(success=True, msg="Data successfully fetched and processed.")

        except RateLimitError:
            self._handle_rate_limit(keyword, start_date, end_date)
        except Exception as e:
            self._on_search_finished(success=False, msg=f"An error occurred: {str(e)}")

    def _handle_rate_limit(self, keyword, start_date, end_date):
        if self.stop_event.is_set():
             self._on_search_finished(success=False, msg="Search stopped by user.")
             return
             
        self.log("Rate Limit Reached!")
        # We must schedule GUI interactions on the main thread
        self.root.after(0, self._show_rate_limit_dialog, keyword, start_date, end_date)

    def _show_rate_limit_dialog(self, keyword, start_date, end_date):
        dialog = tk.Toplevel(self.root)
        dialog.title("API Limit Reached")
        dialog.geometry("350x150")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="GDELT API rate limit reached.\nHow would you like to proceed?", pady=10).pack()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        def retry_now():
            dialog.destroy()
            self.log("Retrying immediately...")
            threading.Thread(target=self._fetch_data, args=(keyword, start_date, end_date), daemon=True).start()

        def wait_and_retry(minutes):
            dialog.destroy()
            self.log(f"Waiting for {minutes} minutes before retrying...")
            threading.Thread(target=self._wait_timer, args=(minutes, keyword, start_date, end_date), daemon=True).start()

        def cancel():
            dialog.destroy()
            self._on_search_finished(success=False, msg="Search cancelled due to rate limit.")

        tk.Button(btn_frame, text="Retry Now", command=retry_now).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Wait 5 Min", command=lambda: wait_and_retry(5)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Wait 15 Min", command=lambda: wait_and_retry(15)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Stop", command=cancel).pack(side=tk.LEFT, padx=5)

    def _wait_timer(self, minutes, keyword, start_date, end_date):
        seconds = minutes * 60
        for i in range(seconds):
            if self.stop_event.is_set():
                self._on_search_finished(success=False, msg="Wait cancelled by user.")
                return
            
            if i % 60 == 0:
                mins_left = (seconds - i) // 60
                self.log(f"Waiting... {mins_left} minutes left.")
            time.sleep(1)
            
        self.log("Wait complete. Retrying...")
        self._fetch_data(keyword, start_date, end_date)

    def _on_search_finished(self, success, msg):
        self.is_fetching = False
        
        # Schedule GUI updates on the main thread
        def update_gui():
            self.log(msg)
            self.search_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
            if success and self.df is not None:
                self.export_btn.config(state=tk.NORMAL)
                self._plot_data()
        
        self.root.after(0, update_gui)

    def _plot_data(self):
        self.ax.clear()
        
        if self.df is not None and not self.df.empty:
            self.ax.plot(self.df['date'], self.df['volume'], color='blue', linewidth=1.5)
            self.ax.set_title(f"Media Coverage Volume Intensity", fontsize=12)
            self.ax.set_xlabel("Date", fontsize=10)
            self.ax.set_ylabel("Relative Coverage (%)", fontsize=10)
            self.ax.grid(True, linestyle='--', alpha=0.7)
            
            # Rotate x-axis dates for better readability
            self.fig.autofmt_xdate()
            
            self.canvas.draw()
            self.log("Plot updated.")

    def export_csv(self):
        if self.df is None or self.df.empty:
            messagebox.showwarning("Export Error", "No data to export.")
            return
            
        keyword = self.keyword_entry.get().strip().replace(" ", "_")
        default_filename = f"gdelt_trend_{keyword}.csv"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_filename,
            title="Save Data to CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if filepath:
            try:
                self.df.to_csv(filepath, index=False)
                self.log(f"Data exported successfully to: {filepath}")
                messagebox.showinfo("Export Success", "Data exported successfully! It is now ready for Power BI.")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save file:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GdeltApp(root)
    root.mainloop()
