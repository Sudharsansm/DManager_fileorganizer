
import os
import sys
import time
import shutil
import hashlib
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# -------------------- Helpers --------------------
def human_size(n):
    for unit in ['B','KB','MB','GB','TB']:
        if abs(n) < 1024.0:
            return "%3.1f %s" % (n, unit)
        n /= 1024.0
    return "%.1f PB" % n

def list_drives():
    drives = []
    try:
        if sys.platform.startswith("win"):
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                d = Path(f"{letter}:\\")
                if d.exists():
                    drives.append(str(d))
        else:
            drives.append(str(Path("/")))
            home = Path.home()
            if str(home) not in drives:
                drives.append(str(home))
    except Exception:
        drives = [str(Path.home())]
    return drives

def md5_for_file(path, block_size=65536):
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(block_size), b""):
                h.update(block)
        return h.hexdigest()
    except Exception:
        return None

# mapping of categories -> extensions (lowercase)
CATEGORY_EXT = {
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp", ".svg"},
    "Videos": {".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv", ".webm"},
    "Documents": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md", ".odt"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "Music": {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"},
}

def categorize_path(p: Path):
    if p.is_dir():
        return "Folders"
    ext = p.suffix.lower()
    for cat, exts in CATEGORY_EXT.items():
        if ext in exts:
            return cat
    return "Files"

# -------------------- FileManagerPro Page --------------------
class FileManagerProPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.current_path = Path.home()
        self.cat_var = tk.StringVar(value="All")

        # sources stored as list of Path strings
        self.sources = []
        # undo stack: list of ops to reverse. Each op is dict: {"type":"move"/"copy", "src":Path, "dst":Path}
        self.undo_stack = []

        self._build_ui()
        self._populate_drives()
        self.change_directory(self.current_path)

    # -------------------- Build UI --------------------
    def _build_ui(self):
        # Drive & Path
        top_frame = ttk.Frame(self)
        top_frame.pack(side="top", fill="x", padx=5, pady=5)

        ttk.Label(top_frame, text="Drive:").pack(side="left")
        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(top_frame, textvariable=self.drive_var, state="readonly", width=30)
        self.drive_combo.pack(side="left", padx=5)
        self.drive_combo.bind("<<ComboboxSelected>>", lambda e: self.change_directory(self.drive_var.get()))

        ttk.Label(top_frame, text=" Path:").pack(side="left", padx=(10,0))
        self.path_entry = ttk.Entry(top_frame, width=70)
        self.path_entry.pack(side="left", padx=5)
        self.path_entry.bind("<Return>", lambda e: self.change_directory(self.path_entry.get()))
        ttk.Button(top_frame, text="Browse", command=self.browse_path).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Go", command=lambda: self.change_directory(self.path_entry.get())).pack(side="left", padx=5)

        # Sources & Actions
        src_frame = ttk.LabelFrame(self, text="Sources & Actions")
        src_frame.pack(fill="x", padx=5, pady=5)

        self.sources_listbox = tk.Listbox(src_frame, height=6)
        self.sources_listbox.pack(fill="x", padx=5, pady=5)

        btn_frame = ttk.Frame(src_frame)
        btn_frame.pack(fill="x", padx=5, pady=2)
        for text, cmd in [("Add Folder", self.add_source_folder),
                          ("Add File", self.add_source_file),
                          ("Remove", self.remove_selected_source),
                          ("Detect Duplicates", self.detect_duplicates),
                          ("Preview (from sources)", self.preview_from_sources),
                          ("Organize", self.organize)]:
            ttk.Button(btn_frame, text=text, command=cmd).pack(side="left", padx=3, pady=2)

        tgt_frame = ttk.Frame(src_frame)
        tgt_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(tgt_frame, text="Target Folder:").pack(side="left")
        self.target_entry = ttk.Entry(tgt_frame, width=50)
        self.target_entry.pack(side="left", padx=5)
        ttk.Button(tgt_frame, text="Browse Target", command=self.browse_target).pack(side="left", padx=5)
        ttk.Button(tgt_frame, text="Undo Last Operation", command=self.undo_last).pack(side="left", padx=5)

        # Categories
        cat_frame = ttk.LabelFrame(self, text="Categories")
        cat_frame.pack(fill="x", padx=5, pady=5)
        cats = ["All", "Images", "Videos", "Documents", "Archives", "Music", "Folders", "Files"]
        for c in cats:
            ttk.Radiobutton(cat_frame, text=c, value=c, variable=self.cat_var, command=self.on_category_change).pack(side="left", padx=5, pady=2)

        # Treeview
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        cols = ("Name", "Type", "Size", "Modified")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="extended")
        for c in cols:
            self.tree.heading(c, text=c)
            # adjust widths a bit
            self.tree.column(c, width=200 if c=="Name" else 120)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_item_open)

        # Bottom Buttons
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", padx=5, pady=5)
        for text, cmd in [("Upload File Here", self.upload_here),
                          ("Create Folder", self.create_folder),
                          ("Move Selected", self.move_selected),
                          ("Preview Selected", self.preview_selected)]:
            ttk.Button(bottom_frame, text=text, command=cmd).pack(side="left", padx=5)

        # Info
        info_frame = ttk.Frame(self)
        info_frame.pack(fill="x", padx=5, pady=5)
        self.info_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.info_var).pack(side="left")

    def browse_path(self):
        """Opens a directory dialog and changes to that folder."""
        folder = filedialog.askdirectory(title="Select Folder to Open")
        if folder:
            self.change_directory(folder)

    # -------------------- Core Methods --------------------
    def _populate_drives(self):
        drives = list_drives()
        self.drive_combo['values'] = drives
        if drives:
            try:
                self.drive_combo.current(0)
                self.drive_var.set(drives[0])
            except Exception:
                pass

    def change_directory(self, path):
        try:
            p = Path(path).expanduser()
            if not p.exists():
                messagebox.showerror("Error", f"Path does not exist: {p}")
                return
            self.current_path = p
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, str(p))
            self._populate_tree()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _populate_tree(self):
        try:
            self.tree.delete(*self.tree.get_children())
            items = sorted(self.current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            filter_cat = self.cat_var.get()
            count = 0
            for e in items:
                cat = categorize_path(e)
                if filter_cat != "All" and cat != filter_cat:
                    continue
                typ = "Folder" if e.is_dir() else e.suffix
                size = "" if e.is_dir() else human_size(e.stat().st_size)
                mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e.stat().st_mtime))
                self.tree.insert("", "end", values=(e.name, typ, size, mtime), iid=str(e))
                count += 1
            self.info_var.set(f"{count} items in {self.current_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_category_change(self):
        self._populate_tree()

    def on_item_open(self, event=None):
        sel = self.tree.focus()
        if sel:
            p = Path(sel)
            if p.is_dir():
                self.change_directory(p)
            else:
                self._open_with_default(p)

    # ---------- Implemented Methods ----------
    def add_source_folder(self):
        d = filedialog.askdirectory(title="Select source folder")
        if d:
            p = str(Path(d))
            if p not in self.sources:
                self.sources.append(p)
                self.sources_listbox.insert(tk.END, p)
            else:
                messagebox.showinfo("Info", "Folder already added.")

    def add_source_file(self):
        files = filedialog.askopenfilenames(title="Select source file(s)")
        for f in files:
            p = str(Path(f))
            if p not in self.sources:
                self.sources.append(p)
                self.sources_listbox.insert(tk.END, p)
        if not files:
            return

    def remove_selected_source(self):
        sel = self.sources_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "No source selected to remove.")
            return
        idx = sel[0]
        val = self.sources_listbox.get(idx)
        self.sources_listbox.delete(idx)
        try:
            self.sources.remove(val)
        except ValueError:
            pass

    def detect_duplicates(self):
        if not self.sources:
            messagebox.showinfo("Info", "No sources added.")
            return
        # gather files
        file_map = {}  # md5 -> list of paths
        total = 0
        for s in list(self.sources):
            p = Path(s)
            if p.is_dir():
                for root, _, files in os.walk(p):
                    for fname in files:
                        fpath = Path(root) / fname
                        total += 1
                        h = md5_for_file(fpath)
                        if h:
                            file_map.setdefault(h, []).append(str(fpath))
            elif p.is_file():
                total += 1
                h = md5_for_file(p)
                if h:
                    file_map.setdefault(h, []).append(str(p))
        duplicates = {k:v for k,v in file_map.items() if len(v) > 1}
        if not duplicates:
            messagebox.showinfo("Duplicates", f"No duplicates found in {len(self.sources)} sources ({total} files scanned).")
            return
        # Show duplicates in a simple dialog
        out_lines = []
        for h, paths in duplicates.items():
            out_lines.append("----")
            out_lines.append(f"Hash: {h}")
            out_lines.extend(paths)
        txt = "\n".join(out_lines)
        # For long text, open a Toplevel with Text widget
        d = tk.Toplevel(self)
        d.title("Duplicates found")
        t = tk.Text(d, width=100, height=30)
        t.pack(fill="both", expand=True)
        t.insert("1.0", txt)
        t.config(state="disabled")

    def preview_from_sources(self):
        # open the first file-like source or first file under first folder
        if not self.sources:
            messagebox.showinfo("Info", "No sources added.")
            return
        for s in self.sources:
            p = Path(s)
            if p.is_file():
                self._open_with_default(p)
                return
            elif p.is_dir():
                # try to find a previewable file
                for root, _, files in os.walk(p):
                    if files:
                        self._open_with_default(Path(root) / files[0])
                        return
        messagebox.showinfo("Info", "No previewable files found in sources.")

    def organize(self):
        target = self._get_target_folder()
        if not target:
            return
        if not self.sources:
            messagebox.showinfo("Info", "No sources to organize.")
            return

        moved = 0
        for s in list(self.sources):
            p = Path(s)
            if p.is_dir():
                for root, _, files in os.walk(p):
                    for fname in files:
                        src = Path(root) / fname
                        cat = categorize_path(src)
                        dest_dir = Path(target) / cat
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        dst = dest_dir / src.name
                        # avoid overwrite: if exists, rename
                        dst = self._unique_path(dst)
                        try:
                            shutil.move(str(src), str(dst))
                            self.undo_stack.append({"type":"move", "src":dst, "dst":src})  # to undo, move back
                            moved += 1
                        except Exception as e:
                            print("organize move error:", e)
            elif p.is_file():
                cat = categorize_path(p)
                dest_dir = Path(target) / cat
                dest_dir.mkdir(parents=True, exist_ok=True)
                dst = dest_dir / p.name
                dst = self._unique_path(dst)
                try:
                    shutil.move(str(p), str(dst))
                    self.undo_stack.append({"type":"move", "src":dst, "dst":p})
                    moved += 1
                except Exception as e:
                    print("organize move error:", e)

        messagebox.showinfo("Organize", f"Organized {moved} files into {target} (by category).")
        # refresh tree (if current path changed by moves)
        self._populate_tree()

    def browse_target(self):
        d = filedialog.askdirectory(title="Select target folder")
        if d:
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, str(Path(d)))

    def undo_last(self):
        if not self.undo_stack:
            messagebox.showinfo("Undo", "No operations to undo.")
            return
        op = self.undo_stack.pop()
        try:
            if op["type"] == "move":
                # op stored as {"type":"move","src":dstPathAfterMove,"dst":originalSrcPath}
                src = Path(op["src"])
                dst = Path(op["dst"])
                # if the original parent doesn't exist, create it
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                messagebox.showinfo("Undo", f"Moved back {src} -> {dst}")
            elif op["type"] == "copy":
                # delete the copied file
                src = Path(op["src"])
                if src.exists():
                    src.unlink()
                    messagebox.showinfo("Undo", f"Removed copied file {src}")
            else:
                messagebox.showinfo("Undo", "Unknown operation to undo.")
        except Exception as e:
            messagebox.showerror("Undo Error", str(e))
        finally:
            self._populate_tree()

    def upload_here(self):
        files = filedialog.askopenfilenames(title="Select file(s) to upload into current folder")
        if not files:
            return
        copied = 0
        for f in files:
            src = Path(f)
            dst = self.current_path / src.name
            dst = self._unique_path(dst)
            try:
                shutil.copy2(str(src), str(dst))
                self.undo_stack.append({"type":"copy", "src":dst})
                copied += 1
            except Exception as e:
                print("upload error:", e)
        messagebox.showinfo("Upload", f"Copied {copied} files to {self.current_path}")
        self._populate_tree()

    def create_folder(self):
        name = simpledialog.askstring("Create folder", "Enter new folder name:", parent=self)
        if not name:
            return
        newp = self.current_path / name
        try:
            newp.mkdir(parents=False, exist_ok=False)
            messagebox.showinfo("Create Folder", f"Created {newp}")
            self._populate_tree()
        except FileExistsError:
            messagebox.showwarning("Create Folder", "Folder already exists.")
        except Exception as e:
            messagebox.showerror("Create Folder", str(e))

    def move_selected(self):
        target = self._get_target_folder()
        if not target:
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Move", "No items selected.")
            return
        moved = 0
        for item_iid in sel:
            src = Path(item_iid)
            if not src.exists():
                continue
            dst = Path(target) / src.name
            dst = self._unique_path(dst)
            try:
                if src.is_dir():
                    shutil.move(str(src), str(dst))
                else:
                    shutil.move(str(src), str(dst))
                # store undo as moving back
                self.undo_stack.append({"type":"move", "src":dst, "dst":src})
                moved += 1
            except Exception as e:
                print("move_selected error:", e)
        messagebox.showinfo("Move", f"Moved {moved} items to {target}")
        self._populate_tree()

    def preview_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Preview", "No item selected.")
            return
        # preview first selected
        p = Path(sel[0])
        if not p.exists():
            messagebox.showwarning("Preview", "Selected item does not exist.")
            return
        if p.is_dir():
            # show folder contents in new window
            try:
                files = list(p.iterdir())
                txt = "\n".join(str(x) for x in files[:200])
                d = tk.Toplevel(self)
                d.title(f"Contents of {p}")
                t = tk.Text(d, width=100, height=30)
                t.pack(fill="both", expand=True)
                t.insert("1.0", txt)
                t.config(state="disabled")
            except Exception as e:
                messagebox.showerror("Preview Error", str(e))
        else:
            self._open_with_default(p)

    # -------------------- Internal utilities --------------------
    def _get_target_folder(self):
        t = self.target_entry.get().strip()
        if not t:
            messagebox.showinfo("Target", "Please select a target folder first.")
            return None
        tp = Path(t)
        if not tp.exists():
            try:
                tp.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Target", f"Cannot create target folder: {e}")
                return None
        return str(tp)

    def _unique_path(self, path: Path) -> Path:
        # If path exists, append suffix like (1), (2)...
        p = Path(path)
        if not p.exists():
            return p
        base = p.stem
        suffix = p.suffix
        parent = p.parent
        i = 1
        while True:
            new_name = f"{base} ({i}){suffix}"
            cand = parent / new_name
            if not cand.exists():
                return cand
            i += 1

    def _open_with_default(self, p: Path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(p))
            elif sys.platform.startswith("darwin"):
                os.system(f"open '{str(p)}'")
            else:
                os.system(f"xdg-open '{str(p)}'")
        except Exception:
            messagebox.showwarning("Open", "Unable to open file.")

# -------------------- Run as standalone app --------------------
def main():
    root = tk.Tk()
    root.title("FileManagerPro")
    root.geometry("1000x700")
    app = FileManagerProPage(root)
    app.pack(fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()
