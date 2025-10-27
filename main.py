import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import dashboard
import file_organizer
import filemanagerpro
import deepscan

# ---------------------- CONFIGURATION ----------------------
CONFIG = {
    "window": {
        "title": "Zaalima Intern App",
        "size": "1000x650",
        "bg": "#f8f8f8"  # main window background
    },
    "sidebar": {
        "width": 250,
        "bg": "#1f2937",
        "title_font": ("Helvetica", 23, "bold"),
        "title_fg": "white",
        "button_bg": "#374151",
        "button_hover_bg": "#4b5563",
        "button_active_bg": "#FFD700",
        "button_fg": "white",
        "button_font": ("Helvetica", 12, "bold"),
        "button_height": 50,
        "padding_y": 8,
        "padding_x": 10
    },
    "topbar": {
        "height": 60,
        "bg": "#1f2937",
        "title_font": ("Helvetica", 16, "bold"),
        "title_fg": "#ffffff",
        "info_font": ("Helvetica", 12),
        "info_fg": "#ffffff",
        "padding_x": 50
    },
    "main_frame": {
        "bg": "#f9fafb"
    },
    "icons": {
        "Dashboard": "icons/dashboard.png",
        "Files Organizer": "icons/organizer.png",
        "My Files": "icons/files.png",
        "Deep Scan": "icons/scan.png"
    }
}

# ---------------------- MAIN APP ----------------------
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(CONFIG["window"]["title"])
        self.geometry(CONFIG["window"]["size"])
        self.configure(bg=CONFIG["window"]["bg"])

        # Pages and active button
        self.pages = {}
        self.active_button = None
        self.sidebar_buttons = {}
        self.icons = {}

        self.load_icons()
        self.create_sidebar()
        self.create_topbar()
        self.create_main_frame()
        self.initialize_pages()

    # ---------------------- Load Icons ----------------------
    def load_icons(self):
        for name, path in CONFIG["icons"].items():
            try:
                img = Image.open(path).resize((20, 20), Image.ANTIALIAS)
                self.icons[name] = ImageTk.PhotoImage(img)
            except Exception:
                self.icons[name] = None

    # ---------------------- Sidebar ----------------------
    def create_sidebar(self):
        cfg = CONFIG["sidebar"]
        self.sidebar = tk.Frame(self, bg=cfg["bg"], width=cfg["width"])
        self.sidebar.pack_propagate(False)  # Keep width
        self.sidebar.pack(side="left", fill="y")

        title = tk.Label(
            self.sidebar,
            text="Zaalima",
            bg=cfg["bg"],
            fg=cfg["title_fg"],
            font=cfg["title_font"]
        )
        title.pack(pady=30)

        # Buttons info
        self.buttons_info = [
            ("Dashboard", self.show_dashboard),
            ("Files Organizer", self.show_fileorganizer),
            ("My Files", self.show_files),
            ("Deep Scan", self.show_deepscan),
        ]

        for text, command in self.buttons_info:
            frame = tk.Frame(self.sidebar, bg=cfg["button_bg"], height=cfg["button_height"])
            frame.pack_propagate(False)  # Keep button height
            frame.pack(fill="x", pady=cfg["padding_y"], padx=cfg["padding_x"])

            icon_label = tk.Label(frame, image=self.icons.get(text), bg=cfg["button_bg"])
            icon_label.pack(side="left", padx=8)

            btn = tk.Label(
                frame,
                text=text,
                bg=cfg["button_bg"],
                fg=cfg["button_fg"],
                font=cfg["button_font"],
                padx=5,
                pady=12,
                cursor="hand2",
                anchor="w"
            )
            btn.pack(side="left", fill="x", expand=True)
            btn.bind("<Button-1>", lambda e, cmd=command, b=btn, t=text: self.set_active(cmd, b, t))
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=cfg["button_hover_bg"] if b != self.active_button else cfg["button_active_bg"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=cfg["button_active_bg"] if b == self.active_button else cfg["button_bg"]))

            self.sidebar_buttons[text] = btn

    # ---------------------- Topbar ----------------------
    def create_topbar(self):
        cfg = CONFIG["topbar"]
        self.topbar = tk.Frame(self, bg=cfg["bg"], height=cfg["height"])
        self.topbar.pack_propagate(False)  # Keep height
        self.topbar.pack(side="top", fill="x")

        self.page_title = tk.Label(
            self.topbar,
            text="Dashboard",
            bg=cfg["bg"],
            fg=cfg["title_fg"],
            font=cfg["title_font"]
        )
        self.page_title.pack(side="left", padx=cfg["padding_x"])

        self.top_info = tk.Label(
            self.topbar,
            text="Welcome to DManager",
            bg=cfg["bg"],
            fg=cfg["info_fg"],
            font=cfg["info_font"]
        )
        self.top_info.pack(side="right", padx=cfg["padding_x"])

    # ---------------------- Main Frame ----------------------
    def create_main_frame(self):
        cfg = CONFIG["main_frame"]
        self.main_frame = tk.Frame(self, bg=cfg["bg"])
        self.main_frame.pack(side="right", fill="both", expand=True)

    # ---------------------- Pages ----------------------
    def initialize_pages(self):
        try:
            self.pages["Dashboard"] = dashboard.DashboardPage(self.main_frame)
            self.pages["Files Organizer"] = file_organizer.FileOrganizerPage(self.main_frame)
            self.pages["My Files"] = filemanagerpro.FileManagerProPage(self.main_frame)
            self.pages["Deep Scan"] = deepscan.create_deepscan_frame(self.main_frame)
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to load UI: {e}")

        # Show default page
        self.set_active(self.show_dashboard, self.sidebar_buttons["Dashboard"], "Dashboard")

    # ---------------------- Navigation ----------------------
    def set_active(self, command, button, page_name):
        cfg = CONFIG["sidebar"]
        if self.active_button:
            self.active_button.config(bg=cfg["button_bg"])
        self.active_button = button
        self.active_button.config(bg=cfg["button_active_bg"])
        self.page_title.config(text=page_name)
        command()

    def clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.pack_forget()

    # ---------------------- Show Pages ----------------------
    def show_dashboard(self):
        self.clear_main()
        frame = self.pages.get("Dashboard")
        if frame:
            frame.pack(fill="both", expand=True)

    def show_fileorganizer(self):
        self.clear_main()
        frame = self.pages.get("Files Organizer")
        if frame:
            frame.pack(fill="both", expand=True)

    def show_files(self):
        self.clear_main()
        frame = self.pages.get("My Files")
        if frame:
            frame.pack(fill="both", expand=True)

    def show_deepscan(self):
        self.clear_main()
        frame = self.pages.get("Deep Scan")
        if frame:
            frame.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
