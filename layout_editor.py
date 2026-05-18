#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import json
import os

LAYOUT_FILE = "/home/edopex/Documents/TURZX/turing-smart-screen-python/layout.json"
DEFAULT_LAYOUT = {
  "fps_title": {"x": 80, "y": 110, "size": 36, "bold": True, "visible": True},
  "fps_val": {"x": 170, "y": 110, "size": 36, "bold": True, "visible": True},
  "fps_ms": {"x": 310, "y": 120, "size": 36, "bold": True, "visible": True},
  "cpu_title": {"x": 480, "y": 110, "size": 36, "bold": True, "visible": True},
  "cpu_val": {"x": 560, "y": 200, "size": 36, "bold": True, "visible": True},
  "cpu_temp": {"x": 700, "y": 210, "size": 36, "bold": True, "visible": True},
  "cpu_power": {"x": 560, "y": 290, "size": 36, "bold": True, "visible": True},
  "cpu_mhz": {"x": 680, "y": 290, "size": 36, "bold": True, "visible": True},
  "gpu_title": {"x": 880, "y": 110, "size": 36, "bold": True, "visible": True},
  "gpu_val": {"x": 960, "y": 200, "size": 36, "bold": True, "visible": True},
  "gpu_temp": {"x": 1100, "y": 210, "size": 36, "bold": True, "visible": True},
  "gpu_power": {"x": 960, "y": 290, "size": 36, "bold": True, "visible": True},
  "gpu_mhz": {"x": 1080, "y": 290, "size": 36, "bold": True, "visible": True},
  "gpu_volt_fan": {"x": 960, "y": 290, "size": 36, "bold": True, "visible": True},
  "gpu_power_desc": {"x": 1190, "y": 210, "size": 36, "bold": True, "visible": True},
  "mem_title": {"x": 1280, "y": 110, "size": 36, "bold": True, "visible": True},
  "ram_used": {"x": 1280, "y": 200, "size": 36, "bold": True, "visible": True},
  "vram_used": {"x": 1490, "y": 200, "size": 36, "bold": True, "visible": True},
  "net_stat": {"x": 1280, "y": 290, "size": 36, "bold": True, "visible": True},
  "sys_title": {"x": 1620, "y": 110, "size": 36, "bold": True, "visible": True},
  "sys_time": {"x": 1620, "y": 200, "size": 36, "bold": True, "visible": True},
  "sys_disk": {"x": 1830, "y": 215, "size": 36, "bold": True, "visible": True}
}

SCALE = 0.5
WIDTH, HEIGHT = int(1920 * SCALE), int(480 * SCALE)

class LayoutEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Turing Smart Screen 8.8\" Layout & Properties Editor")
        self.root.configure(bg="#0f0f13")
        self.root.geometry(f"{WIDTH + 340}x{HEIGHT + 140}")
        self.root.resizable(False, False)

        # Selected Key State
        self.selected_key = None
        self.layout = {}
        self.load_layout()

        # Main Layout: Left Area (Editor) and Right Area (Properties Panel)
        main_pan = tk.Frame(root, bg="#0f0f13")
        main_pan.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        left_frame = tk.Frame(main_pan, bg="#0f0f13")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = tk.LabelFrame(main_pan, text=" Element Properties ", fg="#00b4ff", 
                                     bg="#161622", bd=1, padx=15, pady=15, 
                                     font=("Helvetica", 10, "bold"))
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=15, pady=10)

        # Title Label
        title_lbl = tk.Label(left_frame, text="TURING 8.8\" ADVANCED DRAG & PROPERTIES EDITOR", 
                             fg="#00b4ff", bg="#0f0f13", font=("Helvetica", 12, "bold"))
        title_lbl.pack(pady=5)

        # Instructions
        desc_lbl = tk.Label(left_frame, text="Click an element to edit properties. Drag to reposition. Double click a label to toggle visibility.", 
                             fg="#a0a0aa", bg="#0f0f13", font=("Helvetica", 9))
        desc_lbl.pack(pady=2)

        # Canvas
        self.canvas = tk.Canvas(left_frame, width=WIDTH, height=HEIGHT, bg="#16161e", 
                               highlightthickness=1, highlightbackground="#00b4ff")
        self.canvas.pack(padx=10, pady=5)

        # Guidelines (at 50% scale)
        for col_x in [80, 480, 880, 1280, 1620]:
            x = int(col_x * SCALE)
            self.canvas.create_line(x, 0, x, HEIGHT, fill="#252538", dash=(4, 4))
        for row_y in [110, 200, 290]:
            y = int(row_y * SCALE)
            self.canvas.create_line(0, y, WIDTH, y, fill="#252538", dash=(4, 4))

        self.drag_item = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # Build Sidebar Controls in Right Frame
        self.sel_title_lbl = tk.Label(right_frame, text="Selected: None", fg="#ffffff", 
                                      bg="#161622", font=("Helvetica", 11, "bold"))
        self.sel_title_lbl.pack(pady=8)

        # Visibility Toggle
        self.vis_var = tk.BooleanVar(value=True)
        self.vis_chk = tk.Checkbutton(right_frame, text="Visible on Screen", variable=self.vis_var, 
                                      command=self.update_selected_property, fg="#ffffff", bg="#161622", 
                                      activeforeground="#ffffff", activebackground="#161622", 
                                      selectcolor="#161622", font=("Helvetica", 9, "bold"))
        self.vis_chk.pack(anchor=tk.W, pady=8)

        # Font Size
        tk.Label(right_frame, text="Font Size:", fg="#a0a0aa", bg="#161622", font=("Helvetica", 9)).pack(anchor=tk.W, pady=2)
        self.size_scale = tk.Scale(right_frame, from_=12, to=64, resolution=2, orient=tk.HORIZONTAL, 
                                    bg="#161622", fg="#ffffff", highlightthickness=0, bd=0, 
                                    troughcolor="#252538", activebackground="#00b4ff",
                                    command=lambda e: self.update_selected_property())
        self.size_scale.pack(fill=tk.X, pady=4)

        # Bold Toggle
        self.bold_var = tk.BooleanVar(value=True)
        self.bold_chk = tk.Checkbutton(right_frame, text="Bold Weight", variable=self.bold_var, 
                                       command=self.update_selected_property, fg="#ffffff", bg="#161622", 
                                       activeforeground="#ffffff", activebackground="#161622", 
                                       selectcolor="#161622", font=("Helvetica", 9, "bold"))
        self.bold_chk.pack(anchor=tk.W, pady=8)

        # Font Family Dropdown
        tk.Label(right_frame, text="Font Family:", fg="#a0a0aa", bg="#161622", font=("Helvetica", 9)).pack(anchor=tk.W, pady=2)
        self.font_var = tk.StringVar(value="DejaVuSans")
        self.font_menu = tk.OptionMenu(right_frame, self.font_var, *["DejaVuSans", "DejaVuSerif", "LiberationSans", "LiberationMono", "Ubuntu", "Roboto"],
                                       command=lambda e: self.update_selected_property())
        self.font_menu.configure(bg="#1e1e24", fg="#ffffff", activebackground="#2b2b36", activeforeground="#ffffff", 
                                 highlightthickness=0, bd=0, font=("Helvetica", 9, "bold"))
        self.font_menu["menu"].configure(bg="#161622", fg="#ffffff", activebackground="#00b4ff", activeforeground="#ffffff")
        self.font_menu.pack(fill=tk.X, pady=8)

        # Footer Button Controls
        ctrl_frame = tk.Frame(left_frame, bg="#0f0f13")
        ctrl_frame.pack(pady=10)

        reset_btn = tk.Button(ctrl_frame, text="Reset Defaults", command=self.reset_layout, 
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

        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

        # Draw Canvas Elements
        self.draw_elements()
        self.update_sidebar()

    def load_layout(self):
        try:
            if os.path.exists(LAYOUT_FILE):
                with open(LAYOUT_FILE) as f:
                    self.layout = json.load(f)
                    # Complete missing properties dynamically
                    for k, val in DEFAULT_LAYOUT.items():
                        if k not in self.layout:
                            self.layout[k] = val.copy()
                        elif isinstance(self.layout[k], list):
                            # Upgrade from [x, y] coordinates
                            self.layout[k] = {
                                "x": self.layout[k][0],
                                "y": self.layout[k][1],
                                "size": 36,
                                "bold": True,
                                "visible": True,
                                "font": "DejaVuSans"
                            }
                        elif "font" not in self.layout[k]:
                            self.layout[k]["font"] = "DejaVuSans"
                    return
        except Exception as e:
            messagebox.showwarning("Error Loading Layout", f"Could not load layout.json, using defaults.\n{e}")
        self.layout = DEFAULT_LAYOUT.copy()

    def draw_elements(self):
        self.canvas.delete("draggable")
        
        display_texts = {
            "fps_title": "[FPS Title]", "fps_val": "180", "fps_ms": "5.5ms",
            "cpu_title": "[CPU Title]", "cpu_val": "45%", "cpu_temp": "55°C",
            "cpu_power": "42W", "cpu_mhz": "4200MHz",
            "gpu_title": "[GPU Title]", "gpu_val": "78%", "gpu_temp": "62°C",
            "gpu_power": "180W", "gpu_mhz": "1950MHz", "gpu_volt_fan": "1.05V 2100RPM", "gpu_power_desc": "120W",
            "mem_title": "[MEMORY Title]", "ram_used": "7.5G/16.0G", "vram_used": "VRAM 4.2G", "net_stat": "NET ↓240 ↑45 KB/s",
            "sys_title": "[SYSTEM Title]", "sys_time": "12:34:56", "sys_disk": "DISK 35%"
        }
        
        colors = {
            "fps_title": "#00b4ff", "cpu_title": "#00b4ff", "gpu_title": "#00b4ff",
            "mem_title": "#00b4ff", "sys_title": "#00b4ff", "fps_val": "#00ff66", "sys_time": "#ffffff"
        }

        font_family_map = {
            "DejaVuSans": "DejaVu Sans",
            "DejaVuSerif": "DejaVu Serif",
            "LiberationSans": "Liberation Sans",
            "LiberationMono": "Liberation Mono",
            "Ubuntu": "Ubuntu",
            "Roboto": "Roboto"
        }
        for key, prop in self.layout.items():
            x = int(prop.get("x", 0) * SCALE)
            y = int(prop.get("y", 0) * SCALE)
            size = int(prop.get("size", 36) * SCALE)
            bold = prop.get("bold", True)
            visible = prop.get("visible", True)
            font_name = prop.get("font", "DejaVuSans")

            txt = display_texts.get(key, f"[{key}]")
            font_weight = "bold" if bold else "normal"
            font_family = font_family_map.get(font_name, "DejaVu Sans")
            
            # Use distinct visual indicators for active vs disabled (hidden) elements
            if visible:
                color = colors.get(key, "#ffffff")
                if "title" in key:
                    color = "#00b4ff"
                elif "val" in key and key != "fps_val":
                    color = "#ffffff"
                elif key in ["fps_ms", "cpu_temp", "gpu_temp", "ram_used", "vram_used"]:
                    color = "#e0e0e0"
                elif key in ["cpu_power", "gpu_power", "cpu_mhz", "gpu_mhz", "gpu_power_desc"]:
                    color = "#a0a0aa"
            else:
                color = "#454552" # Dark, semi-transparent grey for hidden/disabled elements

            # Create text canvas item
            item = self.canvas.create_text(
                x, y, text=txt, fill=color, 
                font=(font_family, size, font_weight), 
                anchor=tk.NW, tags=("draggable", key)
            )

            # Draw a tiny neon indicator if this is the selected element
            if key == self.selected_key:
                bbox = self.canvas.bbox(item)
                if bbox:
                    self.canvas.create_rectangle(
                        bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, 
                        outline="#00b4ff", width=1, tags=("draggable", "selection_box")
                    )

            # Bind mouse and click events
            self.canvas.tag_bind(item, "<Button-1>", lambda event, k=key, i=item: self.start_drag(event, k, i))
            self.canvas.tag_bind(item, "<B1-Motion>", self.drag)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self.stop_drag)
            self.canvas.tag_bind(item, "<Double-Button-1>", lambda event, k=key: self.toggle_visibility(k))

    def start_drag(self, event, key, item):
        self.selected_key = key
        self.drag_item = item
        self.drag_key = key
        cx, cy = self.canvas.coords(item)
        self.drag_offset_x = event.x - cx
        self.drag_offset_y = event.y - cy
        
        self.update_sidebar()
        
        # Redraw only selection box without wiping other canvas items
        self.canvas.delete("selection_box")
        bbox = self.canvas.bbox(item)
        if bbox:
            self.canvas.create_rectangle(
                bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, 
                outline="#00b4ff", width=1, tags=("draggable", "selection_box")
            )

    def drag(self, event):
        if self.drag_item:
            new_x = max(0, min(event.x - self.drag_offset_x, WIDTH - 10))
            new_y = max(0, min(event.y - self.drag_offset_y, HEIGHT - 10))
            self.canvas.coords(self.drag_item, new_x, new_y)
            
            # Keep selection box aligned during live drag
            self.canvas.delete("selection_box")
            bbox = self.canvas.bbox(self.drag_item)
            if bbox:
                self.canvas.create_rectangle(
                    bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, 
                    outline="#00b4ff", width=1, tags=("draggable", "selection_box")
                )

    def stop_drag(self, event):
        if self.drag_item:
            cx, cy = self.canvas.coords(self.drag_item)
            orig_x = int(cx / SCALE)
            orig_y = int(cy / SCALE)
            self.layout[self.drag_key]["x"] = orig_x
            self.layout[self.drag_key]["y"] = orig_y
            self.drag_item = None
            self.save_layout()
            # Cleanly refresh all elements after release
            self.draw_elements()

    def toggle_visibility(self, key):
        self.layout[key]["visible"] = not self.layout[key]["visible"]
        if self.selected_key == key:
            self.vis_var.set(self.layout[key]["visible"])
        self.save_layout()
        self.draw_elements()

    def update_sidebar(self):
        if self.selected_key:
            prop = self.layout[self.selected_key]
            self.sel_title_lbl.configure(text=f"Selected: {self.selected_key}", fg="#00b4ff")
            self.vis_var.set(prop.get("visible", True))
            self.size_scale.set(prop.get("size", 36))
            self.bold_var.set(prop.get("bold", True))
            self.font_var.set(prop.get("font", "DejaVuSans"))
            
            self.vis_chk.configure(state=tk.NORMAL)
            self.size_scale.configure(state=tk.NORMAL)
            self.bold_chk.configure(state=tk.NORMAL)
            self.font_menu.configure(state=tk.NORMAL)
        else:
            self.sel_title_lbl.configure(text="Selected: None", fg="#a0a0aa")
            self.vis_chk.configure(state=tk.DISABLED)
            self.size_scale.configure(state=tk.DISABLED)
            self.bold_chk.configure(state=tk.DISABLED)
            self.font_menu.configure(state=tk.DISABLED)

    def update_selected_property(self):
        if self.selected_key:
            self.layout[self.selected_key]["visible"] = self.vis_var.get()
            self.layout[self.selected_key]["size"] = self.size_scale.get()
            self.layout[self.selected_key]["bold"] = self.bold_var.get()
            self.layout[self.selected_key]["font"] = self.font_var.get()
            self.save_layout()
            # Redraw selection highlights and font sizes instantly
            self.draw_elements()

    def save_layout(self):
        try:
            with open(LAYOUT_FILE, "w") as f:
                json.dump(self.layout, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error Saving Layout", f"Could not write to layout.json:\n{e}")

    def reset_layout(self):
        if messagebox.askyesno("Reset Coordinates", "Are you sure you want to reset all coordinates and settings to defaults?"):
            self.layout = DEFAULT_LAYOUT.copy()
            self.selected_key = None
            self.update_sidebar()
            self.draw_elements()
            self.save_layout()

if __name__ == "__main__":
    root = tk.Tk()
    app = LayoutEditor(root)
    root.mainloop()
