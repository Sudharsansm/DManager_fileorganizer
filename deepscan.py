import os
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import random
import threading


# -------------------------------
# Risk & Entropy Simulation Utils
# -------------------------------
def calculate_entropy(filename):
    """Fake entropy calculation: random float between 3.5–8.0"""
    return round(random.uniform(3.5, 8.0), 2)


def get_risk_level(entropy, size):
    """Simulate risk level using entropy and file size."""
    if entropy > 7 or size > 5_000_000:
        return "High"
    elif entropy > 5:
        return "Medium"
    else:
        return "Low"


# -------------------------------
# Hash Utility
# -------------------------------
def hash_file(filepath):
    """Return MD5 hash of a file."""
    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return "Error"


# -------------------------------
# Deep Scan Logic
# -------------------------------
def deep_scan(folder_path, progress_callback, result_callback, complete_callback):
    scanned_files = []
    file_list = []

    for root, _, files in os.walk(folder_path):
        for name in files:
            file_list.append(os.path.join(root, name))

    total_files = len(file_list)
    for i, filepath in enumerate(file_list, 1):
        try:
            size = os.path.getsize(filepath)
            entropy = calculate_entropy(filepath)
            risk = get_risk_level(entropy, size)
            file_hash = hash_file(filepath)

            scanned_files.append({
                "filename": os.path.basename(filepath),
                "size": size,
                "risk": risk,
                "entropy": entropy,
                "hash": file_hash
            })
        except Exception as e:
            print(f"Error scanning {filepath}: {e}")

        progress_callback(i, total_files)
        result_callback(scanned_files[-1])

    complete_callback(scanned_files)


# -------------------------------
# Deep Scan UI Frame
# -------------------------------
class DeepScanPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.scan_results = []
        self.filtered_results = []
        self.running = False
        self.configure(style="Card.TFrame")

        self.create_ui()

    def create_ui(self):
        # --- Header ---
        header = ttk.Label(self, text="🧠 Deep Scan – Automated File Risk Analyzer",
                           font=("Helvetica", 16, "bold"))
        header.pack(pady=10)

        # --- Folder Selection ---
        frame_top = ttk.Frame(self)
        frame_top.pack(pady=10, fill='x', padx=20)

        ttk.Label(frame_top, text="📁 Folder Path:").pack(side='left', padx=5)
        self.folder_path = tk.StringVar(value="C:/")
        self.entry_folder = ttk.Entry(frame_top, textvariable=self.folder_path, width=70)
        self.entry_folder.pack(side='left', padx=5)

        ttk.Button(frame_top, text="Browse", command=self.select_folder).pack(side='left', padx=5)
        self.scan_btn = ttk.Button(frame_top, text="Start Scan", command=self.start_scan)
        self.scan_btn.pack(side='left', padx=5)

        # --- Progress Bar ---
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', padx=20, pady=5)

        # --- Filter & Sort ---
        frame_filter = ttk.Frame(self)
        frame_filter.pack(pady=5, fill='x', padx=20)

        ttk.Label(frame_filter, text="🔍 Filter:").pack(side='left', padx=5)
        self.filter_var = tk.StringVar()
        self.filter_var.trace("w", self.apply_filter)
        ttk.Entry(frame_filter, textvariable=self.filter_var, width=30).pack(side='left', padx=5)

        ttk.Label(frame_filter, text="Sort By:").pack(side='left', padx=10)
        self.sort_key = tk.StringVar(value="risk")
        sort_menu = ttk.Combobox(frame_filter, textvariable=self.sort_key,
                                 values=["filename", "size", "risk", "entropy"], width=15)
        sort_menu.pack(side='left', padx=5)

        ttk.Label(frame_filter, text="Order:").pack(side='left', padx=10)
        self.sort_order = tk.StringVar(value="desc")
        order_menu = ttk.Combobox(frame_filter, textvariable=self.sort_order,
                                  values=["asc", "desc"], width=10)
        order_menu.pack(side='left', padx=5)

        ttk.Button(frame_filter, text="Apply Sort", command=self.apply_sort).pack(side='left', padx=10)

        # --- Treeview (Results Table) ---
        columns = ("filename", "size", "risk", "entropy", "hash")
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=160)
        self.tree.pack(fill='both', expand=True, padx=20, pady=10)

        # --- Export & Summary ---
        frame_bottom = ttk.Frame(self)
        frame_bottom.pack(fill='x', pady=10)

        ttk.Button(frame_bottom, text="Export CSV", command=self.export_csv).pack(side='left', padx=10)
        ttk.Button(frame_bottom, text="AI Summary", command=self.show_summary).pack(side='left', padx=10)

    # ------------------ Handlers ------------------
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def start_scan(self):
        if self.running:
            messagebox.showwarning("Warning", "Scan already running!")
            return

        folder = self.folder_path.get()
        if not os.path.exists(folder):
            messagebox.showerror("Error", "Invalid folder path!")
            return

        self.running = True
        self.scan_btn.config(state='disabled')
        self.tree.delete(*self.tree.get_children())
        self.scan_results.clear()

        threading.Thread(target=deep_scan, args=(
            folder,
            self.update_progress,
            self.add_result_row,
            self.scan_complete
        ), daemon=True).start()

    def update_progress(self, current, total):
        percent = (current / total) * 100
        self.progress_var.set(percent)
        self.update_idletasks()

    def add_result_row(self, file_data):
        color = {"High": "#ffcccc", "Medium": "#fff2cc", "Low": "#d9ead3"}[file_data["risk"]]
        self.tree.insert("", "end",
                         values=(file_data["filename"], file_data["size"], file_data["risk"],
                                 file_data["entropy"], file_data["hash"]),
                         tags=(file_data["risk"],))
        self.tree.tag_configure(file_data["risk"], background=color)
        self.scan_results.append(file_data)
        self.filtered_results = self.scan_results

    def scan_complete(self, results):
        self.running = False
        self.scan_btn.config(state='normal')
        messagebox.showinfo("Scan Complete", f"Scanned {len(results)} files successfully!")

    def apply_filter(self, *args):
        query = self.filter_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for item in self.scan_results:
            if query in item["filename"].lower():
                self.tree.insert("", "end",
                                 values=(item["filename"], item["size"], item["risk"],
                                         item["entropy"], item["hash"]))
        self.filtered_results = [f for f in self.scan_results if query in f["filename"].lower()]

    def apply_sort(self):
        key = self.sort_key.get()
        reverse = self.sort_order.get() == "desc"
        self.filtered_results.sort(
            key=lambda x: x[key] if key != "risk" else {"High": 3, "Medium": 2, "Low": 1}[x["risk"]],
            reverse=reverse)
        self.tree.delete(*self.tree.get_children())
        for f in self.filtered_results:
            self.tree.insert("", "end",
                             values=(f["filename"], f["size"], f["risk"], f["entropy"], f["hash"]))

    def export_csv(self):
        if not self.filtered_results:
            messagebox.showwarning("Warning", "No data to export!")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv",
                                                filetypes=[("CSV Files", "*.csv")])
        if not filepath:
            return
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.filtered_results[0].keys())
            writer.writeheader()
            writer.writerows(self.filtered_results)
        messagebox.showinfo("Export Complete", f"Data exported to {filepath}")

    def show_summary(self):
        high = sum(1 for f in self.scan_results if f["risk"] == "High")
        med = sum(1 for f in self.scan_results if f["risk"] == "Medium")
        low = sum(1 for f in self.scan_results if f["risk"] == "Low")
        messagebox.showinfo("AI Summary",
                            f"🧠 AI Summary:\n\nHigh Risk Files: {high}\nMedium Risk Files: {med}\nLow Risk Files: {low}")


# -------------------------------
# Integration Helper for Main App
# -------------------------------
def create_deepscan_frame(parent):
    """Return a DeepScanPage instance for embedding in main app."""
    return DeepScanPage(parent)


# -------------------------------
# Standalone Run Mode
# -------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.title("DeepScan – Automated File Risk Analyzer")
    root.geometry("950x600")
    app = DeepScanPage(root)
    app.pack(fill="both", expand=True)
    root.mainloop()
