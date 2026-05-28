class AnalysisWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Analysis")
        self.window.geometry("400x300")

        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()

    def _build_ui(self):
        tk.Label(self.window, text="Analysis Options", font=("Arial", 14)).pack(pady=10)

       