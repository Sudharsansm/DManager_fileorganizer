# FileOrganizerPro.py

import os
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import hashlib
import json
import customtkinter as ctk

# --------------------------
# File Organizer Page (Integrated with DManager)
# --------------------------
class FileOrganizerPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        import json
        import hashlib
        import shutil
        from pathlib import Path

        # -------------------- Configuration --------------------
        self.CATEGORIES = {
            "Documents": [".pdf", ".docx", ".txt", ".pptx", ".xlsx", ".csv"],
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
            "Videos": [".mp4", ".mkv", ".avi", ".mov"],
            "Music": [".mp3", ".wav", ".flac"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Programs": [".exe", ".msi", ".bat", ".sh"],
        }
        self.UNDO_LOG_FILE = "undo_log.json"

        self.sources = []
        self.target_folder = ""
        self.undo_log = []

        self.subfolders_var = tk.IntVar(value=1)

        self.create_ui()

    # -------------------- Helper Functions --------------------
    def hash_file(self, file_path):
        h = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()

    def move_file(self, src, dst):
        dst_path = Path(dst)
        if dst_path.exists():
            base, ext = dst_path.stem, dst_path.suffix
            counter = 1
            while dst_path.exists():
                dst_path = dst_path.with_name(f"{base}({counter}){ext}")
                counter += 1
        shutil.move(src, dst_path)
        return str(dst_path)

    def add_folder(self, folder_path):
        folder_path = str(Path(folder_path).resolve())
        if folder_path not in self.sources:
            self.sources.append(folder_path)
            self.sources_listbox.insert(tk.END, folder_path)

    def add_file(self, file_path):
        file_path = str(Path(file_path).resolve())
        if file_path not in self.sources:
            self.sources.append(file_path)
            self.sources_listbox.insert(tk.END, file_path)

    def remove_selected(self):
        selected = self.sources_listbox.curselection()
        for i in reversed(selected):
            path = self.sources_listbox.get(i)
            if path in self.sources:
                self.sources.remove(path)
            self.sources_listbox.delete(i)

    def clear_sources(self):
        self.sources.clear()
        self.sources_listbox.delete(0, tk.END)

    def set_target(self, folder_path):
        if folder_path:
            self.target_folder = str(Path(folder_path).resolve())
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, self.target_folder)

    def preview_files(self):
        self.preview_listbox.delete(0, tk.END)
        files = []
        for path in self.sources:
            p = Path(path)
            if p.is_dir():
                for f in p.rglob("*"):
                    if f.is_file():
                        files.append(str(f))
            elif p.is_file():
                files.append(str(p))
        for f in files:
            self.preview_listbox.insert(tk.END, f)
        messagebox.showinfo("Preview", f"{len(files)} files detected for organization.")

    def detect_duplicates(self):
        file_hashes = {}
        duplicates = []
        for path in self.sources:
            p = Path(path)
            if p.is_dir():
                for f in p.rglob("*"):
                    if f.is_file():
                        h = self.hash_file(f)
                        if h in file_hashes:
                            duplicates.append((str(f), file_hashes[h]))
                        else:
                            file_hashes[h] = str(f)
            elif p.is_file():
                h = self.hash_file(p)
                if h in file_hashes:
                    duplicates.append((str(p), file_hashes[h]))
                else:
                    file_hashes[h] = str(p)
        return duplicates

    def organize_files(self):
        if not self.target_folder:
            messagebox.showerror("Error", "Target folder not set!")
            return
        if not self.sources:
            messagebox.showerror("Error", "No source files/folders selected!")
            return

        self.undo_log = []
        for path in self.sources:
            p = Path(path)
            if p.is_dir():
                for f in p.rglob("*"):
                    if f.is_file():
                        self._move_file(f)
            elif p.is_file():
                self._move_file(p)

        with open(self.UNDO_LOG_FILE, "w") as f:
            json.dump(self.undo_log, f, indent=2)

        self.preview_listbox.delete(0, tk.END)
        messagebox.showinfo("Organize", f"Files organized successfully! ({len(self.undo_log)} files moved)")

    def _move_file(self, file_path):
        target = Path(self.target_folder)
        category_folder = None
        if self.subfolders_var.get():
            for cat, exts in self.CATEGORIES.items():
                if file_path.suffix.lower() in exts:
                    category_folder = target / cat
                    category_folder.mkdir(exist_ok=True)
                    break
            if not category_folder:
                category_folder = target / "Others"
                category_folder.mkdir(exist_ok=True)
        dst = category_folder / file_path.name if category_folder else target / file_path.name
        new_dst = self.move_file(file_path, dst)
        self.undo_log.append({"src": new_dst, "dst": str(file_path)})

    def undo(self):
        if not Path(self.UNDO_LOG_FILE).exists():
            messagebox.showinfo("Undo", "No undo log found!")
            return
        with open(self.UNDO_LOG_FILE, "r") as f:
            self.undo_log = json.load(f)
        for move in reversed(self.undo_log):
            src = move["src"]
            dst = move["dst"]
            if Path(src).exists():
                self.move_file(src, dst)
        os.remove(self.UNDO_LOG_FILE)
        messagebox.showinfo("Undo", f"Undo completed! ({len(self.undo_log)} files restored)")

    def show_duplicates(self):
        duplicates = self.detect_duplicates()
        self.preview_listbox.delete(0, tk.END)
        if duplicates:
            for dup, orig in duplicates:
                self.preview_listbox.insert(tk.END, f"Duplicate: {dup} | Original: {orig}")
            messagebox.showinfo("Duplicates Found", f"{len(duplicates)} duplicates detected.")
        else:
            messagebox.showinfo("Duplicates", "No duplicates found.")

    # -------------------- UI --------------------
    def create_ui(self):
        # Header
        ctk.CTkLabel(self, text="File Organizer Pro", font=("Arial", 24)).pack(pady=20)

        # Sources Frame
        sources_frame = ctk.CTkFrame(self, fg_color="#2a2a2a", corner_radius=0)
        sources_frame.pack(padx=20, pady=10, fill="x")
        self.sources_listbox = tk.Listbox(sources_frame, height=6)
        self.sources_listbox.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        scrollbar = tk.Scrollbar(sources_frame, command=self.sources_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.sources_listbox.config(yscrollcommand=scrollbar.set)

        # Source Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(btn_frame, text="Add Folder", command=lambda: self.add_folder(filedialog.askdirectory())).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Add File", command=lambda: self.add_file(filedialog.askopenfilename())).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Clear All", command=self.clear_sources).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Detect Duplicates", command=self.show_duplicates).pack(side="left", padx=5)

        # Target Folder
        target_frame = ctk.CTkFrame(self)
        target_frame.pack(fill="x", padx=20, pady=5)
        self.target_entry = ctk.CTkEntry(target_frame, width=400)
        self.target_entry.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(target_frame, text="Browse", command=lambda: self.set_target(filedialog.askdirectory())).pack(side="left", padx=5)
        ctk.CTkCheckBox(target_frame, text="Create subfolders by type", variable=self.subfolders_var).pack(side="left", padx=10)

        # Action Buttons
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(action_frame, text="Preview Files", command=self.preview_files).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="Organize Files", command=self.organize_files).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="Undo Last Operation", command=self.undo).pack(side="left", padx=5)

        # Preview List
        preview_frame = ctk.CTkFrame(self, fg_color="#2a2a2a", corner_radius=0)
        preview_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.preview_listbox = tk.Listbox(preview_frame)
        self.preview_listbox.pack(fill="both", expand=True, padx=5, pady=5)
