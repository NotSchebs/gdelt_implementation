class FiltersWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Filters")
        self.window.geometry("400x300")

        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()

    def _build_ui(self):
        tk.Label(self.window, text="Filter Options", font=("Arial", 14)).pack(pady=10)

        self.english_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.window,
            text="Only English articles",
            variable=self.english_var
        ).pack(anchor="w", padx=20)

        self.sentiment_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.window,
            text="High sentiment only",
            variable=self.sentiment_var
        ).pack(anchor="w", padx=20)

        tk.Button(self.window, text="Close", command=self.window.destroy).pack(pady=20)