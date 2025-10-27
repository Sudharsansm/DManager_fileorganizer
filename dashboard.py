import psutil
import platform
import time
import random
import tkinter as tk
from tkinter import ttk

# -------------------- Helper Function --------------------
def get_system_data():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    uptime = round((time.time() - psutil.boot_time()) / 3600, 2)
    integrity = random.randint(80, 100)
    threats = random.randint(0, 3)
    risk = "Low" if threats == 0 else "Medium" if threats == 1 else "High"
    return cpu, ram, disk, uptime, integrity, threats, risk

# -------------------- Dashboard Page --------------------
class DashboardPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_ui()
        self.update_dashboard()

    # -------------------- Build UI --------------------
    def create_ui(self):
        # Header
        self.header = tk.Label(self, text="System Analyzer Dashboard", font=("Arial", 24, "bold"))
        self.header.pack(pady=20)

        # Main frame for cards
        self.main_frame = tk.Frame(self, bg="#f0f0f0")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Grid layout
        self.main_frame.grid_columnconfigure((0,1,2), weight=1)
        self.main_frame.grid_rowconfigure((0,1), weight=1)

        # Cards
        self.cpu_card = self.create_card(self.main_frame, "CPU Usage", 0, 0)
        self.ram_card = self.create_card(self.main_frame, "RAM Usage", 0, 1)
        self.disk_card = self.create_card(self.main_frame, "Disk Usage", 0, 2)
        self.security_card = self.create_card(self.main_frame, "Security Integrity", 1, 0)
        self.threat_card = self.create_card(self.main_frame, "Threat Level", 1, 1)

        # System Info Card
        self.info_box = tk.Frame(self.main_frame, bg="#e0e0e0", relief="ridge", bd=2)
        self.info_box.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)
        self.info_label = tk.Label(self.info_box, text="", font=("Arial", 14), justify="center")
        self.info_label.pack(pady=20)

    def create_card(self, parent, title, row, col):
        card = tk.Frame(parent, bg="#e0e0e0", relief="ridge", bd=2)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        title_label = tk.Label(card, text=title, font=("Arial", 16, "light"))
        title_label.pack(pady=10)

        progress = ttk.Progressbar(card, orient="horizontal", length=200, mode="determinate")
        progress.pack(pady=10)

        value_label = tk.Label(card, text="10%", font=("Arial", 14))
        value_label.pack(pady=10)

        return {"card": card, "progress": progress, "value_label": value_label}

    # -------------------- Update Dashboard --------------------
    def update_dashboard(self):
        cpu, ram, disk, uptime, integrity, threats, risk = get_system_data()

        self.update_card(self.cpu_card, cpu)
        self.update_card(self.ram_card, ram)
        self.update_card(self.disk_card, disk)
        self.update_card(self.security_card, integrity)

        threat_text = f"{threats} ({risk})"
        self.threat_card["value_label"].configure(text=threat_text)
        self.threat_card["progress"]["value"] = min(threats / 3 * 100, 100)

        sys_name = platform.node()
        os_name = platform.system()
        self.info_label.configure(
            text=f"System: {sys_name}\nOS: {os_name}\nUptime: {uptime} hrs"
        )

        # Refresh every 3 seconds
        self.after(3000, self.update_dashboard)

    def update_card(self, card, value):
        card["progress"]["value"] = value
        card["value_label"].configure(text=f"{value}%")

# -------------------- Run --------------------
def main():
    root = tk.Tk()
    root.title("System Dashboard")
    root.geometry("900x600")
    app = DashboardPage(root)
    app.pack(fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()
import psutil
import platform
import time
import random
import tkinter as tk
from tkinter import ttk

def get_system_data():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    uptime = round((time.time() - psutil.boot_time()) / 3600, 2)
    integrity = random.randint(80, 100)
    threats = random.randint(0, 3)
    risk = "Low" if threats == 0 else "Medium" if threats == 1 else "High"
    return cpu, ram, disk, uptime, integrity, threats, risk

class DashboardPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f8f8f8")
        self.create_ui()
        self.update_dashboard()

    def create_ui(self):
        self.header = tk.Label(self, text="System Analyzer Dashboard", font=("Arial", 24, "bold"), bg="#f8f8f8")
        self.header.pack(pady=20)

        self.main_frame = tk.Frame(self, bg="#f8f8f8")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.main_frame.grid_columnconfigure((0,1,2), weight=1)
        self.main_frame.grid_rowconfigure((0,1), weight=1)

        self.cpu_card = self.create_card(self.main_frame, "CPU Usage", 0, 0)
        self.ram_card = self.create_card(self.main_frame, "RAM Usage", 0, 1)
        self.disk_card = self.create_card(self.main_frame, "Disk Usage", 0, 2)
        self.security_card = self.create_card(self.main_frame, "Security Integrity", 1, 0)
        self.threat_card = self.create_card(self.main_frame, "Threat Level", 1, 1)

        self.info_box = tk.Frame(self.main_frame, bg="#d9d9d9", relief="ridge", bd=2)
        self.info_box.grid(row=1, column=2, sticky="nsew", padx=10, pady=10)
        self.info_label = tk.Label(self.info_box, text="", font=("Arial", 14), bg="white", justify="center")
        self.info_label.pack(fill="both", expand=True, padx=5, pady=5)

    def create_card(self, parent, title, row, col):
        card = tk.Frame(parent, bg="#e6e6e6", relief="ridge", bd=2)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        title_label = tk.Label(card, text=title, font=("Arial", 16, "bold"), bg="white")
        title_label.pack(pady=10, fill="x", padx=5)

        progress = ttk.Progressbar(card, orient="horizontal", length=200, mode="determinate")
        progress.pack(pady=10)

        value_label = tk.Label(card, text="0%", font=("Arial", 14), bg="white")
        value_label.pack(pady=10, fill="x", padx=5)

        return {"card": card, "progress": progress, "value_label": value_label}

    def update_dashboard(self):
        cpu, ram, disk, uptime, integrity, threats, risk = get_system_data()

        self.update_card(self.cpu_card, cpu)
        self.update_card(self.ram_card, ram)
        self.update_card(self.disk_card, disk)
        self.update_card(self.security_card, integrity)

        threat_text = f"{threats} ({risk})"
        self.threat_card["value_label"].configure(text=threat_text)
        self.threat_card["progress"]["value"] = min(threats / 3 * 100, 100)

        sys_name = platform.node()
        os_name = platform.system()
        self.info_label.configure(text=f"System: {sys_name}\nOS: {os_name}\nUptime: {uptime} hrs")

        self.after(3000, self.update_dashboard)

    def update_card(self, card, value):
        card["progress"]["value"] = value
        card["value_label"].configure(text=f"{value}%")

def main():
    root = tk.Tk()
    root.title("System Dashboard")
    root.geometry("900x600")
    app = DashboardPage(root)
    app.pack(fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()
