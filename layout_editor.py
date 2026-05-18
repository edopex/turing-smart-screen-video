#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import json
import os

LAYOUT_FILE = "/home/edopex/Documents/TURZX/turing-smart-screen-python/layout.json"
DEFAULT_LAYOUT = {
  "fps_title": [80, 110],
  "fps_val": [170, 110],
  "fps_ms": [310, 120],
  "cpu_title": [480, 110],
  "cpu_val": [560, 200],
  "cpu_temp": [700, 210],
  "cpu_power": [560, 290],
  "cpu_mhz": [680, 290],
  "gpu_title": [880, 110],
  "gpu_val": [960, 200],
  "gpu_temp": [1100, 210],
  "gpu_power": [960, 290],
  "gpu_mhz": [1080, 290],
  "gpu_volt_fan": [960, 290],
  "gpu_power_desc": [1190, 210],
  "mem_title": [1280, 110],
  "ram_used": [1280, 200],
  "vram_used": [1490, 200],
  "net_stat": [1280, 290],
  "sys_title": [1620, 110],
  "sys_time": [1620, 200],
  "sys_disk": [1830, 215]
}

SCALE = 0.5
WIDTH, HEIGHT = int(1920 * SCALE), int(480 * SCALE)

class LayoutEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Turing Smart Screen 8.8\" Layout Editor")
        self.root.configure(bg="#0f0f13")
        self.root.geometry(f"{WIDTH + 40}x{HEIGHT + 140}")
        self.root.resizable(False, False)

        # Title Label
        title_lbl = tk.Label(root, text="TURING 8.8\" DRAG & DROP LAYOUT EDITOR", 
                             fg="#00b4ff", bg="#0f0f13", font=("Helvetica", 14, "bold"))
        title_lbl.pack(pady=10)

        # Instructions
        desc_lbl = tk.Label(root, text="Drag any element below to reposition it in real-time. Changes are auto-saved to layout.json.", 
                            fg="#a0a0aa", bg="#0f0f13", font=("Helvetica", 9))
        desc_lbl.pack(pady=2)

        # Canvas
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#16161e", 
                               highlightthickness=1, highlightbackground="#00b4ff")
        self.canvas.pack(padx=20, pady=10)

        # Subtle layout grid columns (at 50% scale)
        for col_x in [80, 480, 880, 1280, 1620]:
            x = int(col_x * SCALE)
            self.canvas.create_line(x, 0, x, HEIGHT, fill="#252538", dash=(4, 4))

        # Horizontal guidelines
        for row_y in [110, 200, 290]:
            y = int(row_y * SCALE)
            self.canvas.create_line(0, y, WIDTH, y, fill="#252538", dash=(4, 4))

        self.layout = {}
        self.load_layout()

        self.drag_item = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        self.draw_elements()

        # Controls Frame
        ctrl_frame = tk.Frame(root, bg="#0f0f13")
        ctrl_frame.pack(pady=10)

        reset_btn = tk.Button(ctrl_frame, text="Reset to Defaults", command=self.reset_layout, 
                              fg="#ff4f4f", bg="#1e1e24", activeforeground="#ff4f4f", 
                              activebackground="#2b2b36", highlightthickness=0, bd=0, 
                              padx=15, pady=5, font=("Helvetica", 10, "bold"))
        reset_btn.pack(side=tk.LEFT, padx=10)

        save_btn = tk.Button(ctrl_frame, text="Force Save Layout", command=self.save_layout, 
                             fg="#00ff66", bg="#1e1e24", activeforeground="#00ff66", 
                             activebackground="#2b2b36", highlightthickness=0, bd=0, 
                             padx=15, pady=5, font=("Helvetica", 10, "bold"))
        save_btn.pack(side=tk.LEFT, padx=10)

        close_btn = tk.Button(ctrl_frame, text="Close Editor (X)", command=self.root.destroy, 
                              fg="#ffffff", bg="#1e1e24", activeforeground="#ffffff", 
                              activebackground="#2b2b36", highlightthickness=0, bd=0, 
                              padx=15, pady=5, font=("Helvetica", 10, "bold"))
        close_btn.pack(side=tk.LEFT, padx=10)

        # Bind window manager 'X' button close
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def load_layout(self):
        try:
            if os.path.exists(LAYOUT_FILE):
                with open(LAYOUT_FILE) as f:
                    self.layout = json.load(f)
                    return
        except Exception as e:
            messagebox.showwarning("Error Loading Layout", f"Could not load layout.json, using defaults.\n{e}")
        self.layout = DEFAULT_LAYOUT.copy()

    def draw_elements(self):
        self.canvas.delete("draggable")
        
        # Human-readable representation text for each key
        display_texts = {
            "fps_title": "[FPS Title]",
            "fps_val": "180",
            "fps_ms": "5.5ms",
            "cpu_title": "[CPU Title]",
            "cpu_val": "45%",
            "cpu_temp": "55°C",
            "cpu_power": "42W",
            "cpu_mhz": "4200MHz",
            "gpu_title": "[GPU Title]",
            "gpu_val": "78%",
            "gpu_temp": "62°C",
            "gpu_power": "180W",
            "gpu_mhz": "1950MHz",
            "gpu_volt_fan": "1.05V  2100RPM",
            "gpu_power_desc": "120W",
            "mem_title": "[MEMORY Title]",
            "ram_used": "7.5G/16.0G",
            "vram_used": "VRAM 4.2G",
            "net_stat": "NET ↓240 ↑45 KB/s",
            "sys_title": "[SYSTEM Title]",
            "sys_time": "12:34:56",
            "sys_disk": "DISK 35%"
        }
        
        # Colors for elements
        colors = {
            "fps_title": "#00b4ff",
            "cpu_title": "#00b4ff",
            "gpu_title": "#00b4ff",
            "mem_title": "#00b4ff",
            "sys_title": "#00b4ff",
            "fps_val": "#00ff66",
            "sys_time": "#ffffff"
        }

        for key, coord in self.layout.items():
            x = int(coord[0] * SCALE)
            y = int(coord[1] * SCALE)
            txt = display_texts.get(key, f"[{key}]")
            
            # Larger fonts for main values
            is_main = key in ["fps_val", "cpu_val", "gpu_val", "sys_time"]
            font_size = 12 if is_main else 8
            font_weight = "bold" if (is_main or "title" in key) else "normal"
            
            color = colors.get(key, "#ffffff")
            if "title" in key:
                color = "#00b4ff"
            elif "val" in key and key != "fps_val":
                color = "#ffffff"
            elif key in ["fps_ms", "cpu_temp", "gpu_temp", "ram_used", "vram_used"]:
                color = "#e0e0e0"
            elif key in ["cpu_power", "gpu_power", "cpu_mhz", "gpu_mhz", "gpu_power_desc"]:
                color = "#a0a0aa"
            
            # Create text canvas item
            item = self.canvas.create_text(x, y, text=txt, fill=color, 
                                          font=("Helvetica", font_size, font_weight), 
                                          anchor=tk.NW, tags=("draggable", key))
            
            # Bind events to this item
            self.canvas.tag_bind(item, "<Button-1>", lambda event, k=key, i=item: self.start_drag(event, k, i))
            self.canvas.tag_bind(item, "<B1-Motion>", self.drag)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self.stop_drag)

    def start_drag(self, event, key, item):
        self.drag_item = item
        self.drag_key = key
        # Get current coordinates on the canvas
        cx, cy = self.canvas.coords(item)
        # Calculate mouse offset relative to anchor (NW)
        self.drag_offset_x = event.x - cx
        self.drag_offset_y = event.y - cy

    def drag(self, event):
        if self.drag_item:
            # Set new coordinates, bounded to canvas size
            new_x = max(0, min(event.x - self.drag_offset_x, WIDTH - 10))
            new_y = max(0, min(event.y - self.drag_offset_y, HEIGHT - 10))
            self.canvas.coords(self.drag_item, new_x, new_y)

    def stop_drag(self, event):
        if self.drag_item:
            cx, cy = self.canvas.coords(self.drag_item)
            # Scale coordinates back to 1920x480 space and save
            orig_x = int(cx / SCALE)
            orig_y = int(cy / SCALE)
            self.layout[self.drag_key] = [orig_x, orig_y]
            self.drag_item = None
            self.save_layout()

    def save_layout(self):
        try:
            with open(LAYOUT_FILE, "w") as f:
                json.dump(self.layout, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error Saving Layout", f"Could not write to layout.json:\n{e}")

    def reset_layout(self):
        if messagebox.askyesno("Reset Coordinates", "Are you sure you want to reset all coordinates to their defaults?"):
            self.layout = DEFAULT_LAYOUT.copy()
            self.draw_elements()
            self.save_layout()

if __name__ == "__main__":
    root = tk.Tk()
    app = LayoutEditor(root)
    root.mainloop()
