#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import subprocess
import psutil
import os
import signal
import time

DASHBOARD_PATH = "/home/edopex/Documents/TURZX/turing-smart-screen-python/turing_dashboard.py"
BRIDGE_PATH = "/home/edopex/Documents/TURZX/turing-smart-screen-python/fps_bridge.py"

def find_process(script_path):
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmd = proc.info['cmdline']
            if cmd and len(cmd) >= 2:
                if any(script_path in arg for arg in cmd):
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

class ControlCenter:
    def __init__(self, root):
        self.root = root
        self.root.title("Turing Screen Control Center")
        self.root.configure(bg="#0f0f13")
        self.root.geometry("480x380")
        self.root.resizable(False, False)

        # Title Label
        title_lbl = tk.Label(root, text="TURING SCREEN CONTROL CENTER", 
                             fg="#00b4ff", bg="#0f0f13", font=("Helvetica", 14, "bold"))
        title_lbl.pack(pady=15)

        # Dashboard Card Frame
        self.dash_frame = tk.LabelFrame(root, text=" Turing Screen Dashboard Service ", 
                                         fg="#00b4ff", bg="#161622", bd=1, padx=15, pady=10,
                                         font=("Helvetica", 10, "bold"))
        self.dash_frame.pack(fill=tk.X, padx=25, pady=8)

        self.dash_status_lbl = tk.Label(self.dash_frame, text="STOPPED", fg="#ff4f4f", bg="#161622", 
                                        font=("Helvetica", 11, "bold"))
        self.dash_status_lbl.pack(side=tk.LEFT, padx=10)

        self.dash_start_btn = tk.Button(self.dash_frame, text="Start", command=self.start_dashboard, 
                                        fg="#00ff66", bg="#252538", activeforeground="#00ff66", 
                                        activebackground="#2b2b46", bd=0, padx=15, pady=4, 
                                        font=("Helvetica", 9, "bold"))
        self.dash_start_btn.pack(side=tk.RIGHT, padx=5)

        self.dash_stop_btn = tk.Button(self.dash_frame, text="Stop", command=self.stop_dashboard, 
                                       fg="#ff4f4f", bg="#252538", activeforeground="#ff4f4f", 
                                       activebackground="#2b2b46", bd=0, padx=15, pady=4, 
                                       font=("Helvetica", 9, "bold"))
        self.dash_stop_btn.pack(side=tk.RIGHT, padx=5)

        # Bridge Card Frame
        self.bridge_frame = tk.LabelFrame(root, text=" MangoHud Telemetry Bridge ", 
                                           fg="#00b4ff", bg="#161622", bd=1, padx=15, pady=10,
                                           font=("Helvetica", 10, "bold"))
        self.bridge_frame.pack(fill=tk.X, padx=25, pady=8)

        self.bridge_status_lbl = tk.Label(self.bridge_frame, text="STOPPED", fg="#ff4f4f", bg="#161622", 
                                          font=("Helvetica", 11, "bold"))
        self.bridge_status_lbl.pack(side=tk.LEFT, padx=10)

        self.bridge_start_btn = tk.Button(self.bridge_frame, text="Start", command=self.start_bridge, 
                                          fg="#00ff66", bg="#252538", activeforeground="#00ff66", 
                                          activebackground="#2b2b46", bd=0, padx=15, pady=4, 
                                          font=("Helvetica", 9, "bold"))
        self.bridge_start_btn.pack(side=tk.RIGHT, padx=5)

        self.bridge_stop_btn = tk.Button(self.bridge_frame, text="Stop", command=self.stop_bridge, 
                                         fg="#ff4f4f", bg="#252538", activeforeground="#ff4f4f", 
                                         activebackground="#2b2b46", bd=0, padx=15, pady=4, 
                                         font=("Helvetica", 9, "bold"))
        self.bridge_stop_btn.pack(side=tk.RIGHT, padx=5)

        # Control Panel Footer
        footer_frame = tk.Frame(root, bg="#0f0f13")
        footer_frame.pack(pady=20)

        bg_btn = tk.Button(footer_frame, text="Close to Background", command=self.close_to_bg, 
                            fg="#ffffff", bg="#252538", activeforeground="#ffffff", 
                            activebackground="#2b2b46", bd=0, padx=15, pady=6, 
                            font=("Helvetica", 10, "bold"))
        bg_btn.pack(side=tk.LEFT, padx=10)

        quit_btn = tk.Button(footer_frame, text="Stop All & Exit", command=self.stop_all_and_quit, 
                             fg="#ff4f4f", bg="#1e1e24", activeforeground="#ff4f4f", 
                             activebackground="#2b2b36", bd=0, padx=15, pady=6, 
                             font=("Helvetica", 10, "bold"))
        quit_btn.pack(side=tk.LEFT, padx=10)

        # Start periodic status updates
        self.update_statuses()

    def update_statuses(self):
        # Scan processes for Dashboard
        dash_proc = find_process(DASHBOARD_PATH)
        if dash_proc:
            self.dash_status_lbl.configure(text="RUNNING", fg="#00ff66")
            self.dash_start_btn.configure(state=tk.DISABLED)
            self.dash_stop_btn.configure(state=tk.NORMAL)
        else:
            self.dash_status_lbl.configure(text="STOPPED", fg="#ff4f4f")
            self.dash_start_btn.configure(state=tk.NORMAL)
            self.dash_stop_btn.configure(state=tk.DISABLED)

        # Scan processes for Bridge
        bridge_proc = find_process(BRIDGE_PATH)
        if bridge_proc:
            self.bridge_status_lbl.configure(text="RUNNING", fg="#00ff66")
            self.bridge_start_btn.configure(state=tk.DISABLED)
            self.bridge_stop_btn.configure(state=tk.NORMAL)
        else:
            self.bridge_status_lbl.configure(text="STOPPED", fg="#ff4f4f")
            self.bridge_start_btn.configure(state=tk.NORMAL)
            self.bridge_stop_btn.configure(state=tk.DISABLED)

        # Poll again in 1 second
        self.root.after(1000, self.update_statuses)

    def start_dashboard(self):
        if not find_process(DASHBOARD_PATH):
            try:
                subprocess.Popen(
                    ["python3", DASHBOARD_PATH],
                    cwd=os.path.dirname(DASHBOARD_PATH),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )
                time.sleep(0.5)
                self.update_statuses()
            except Exception as e:
                messagebox.showerror("Error starting Dashboard", str(e))

    def stop_dashboard(self):
        proc = find_process(DASHBOARD_PATH)
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except:
                try:
                    proc.kill()
                except:
                    pass
            time.sleep(0.5)
            self.update_statuses()

    def start_bridge(self):
        if not find_process(BRIDGE_PATH):
            try:
                subprocess.Popen(
                    ["python3", BRIDGE_PATH],
                    cwd=os.path.dirname(BRIDGE_PATH),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )
                time.sleep(0.5)
                self.update_statuses()
            except Exception as e:
                messagebox.showerror("Error starting Bridge", str(e))

    def stop_bridge(self):
        proc = find_process(BRIDGE_PATH)
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except:
                try:
                    proc.kill()
                except:
                    pass
            time.sleep(0.5)
            self.update_statuses()

    def close_to_bg(self):
        self.root.destroy()

    def stop_all_and_quit(self):
        if messagebox.askyesno("Stop All Services", "Are you sure you want to stop all Turing Screen services and exit?"):
            self.stop_dashboard()
            self.stop_bridge()
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ControlCenter(root)
    root.mainloop()
