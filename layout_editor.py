#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import json
import os

LAYOUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "layout.json")
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
  "gpu_volt_fan": {"x": 1190, "y": 210, "size": 36, "bold": True, "visible": True},
  "mem_title": {"x": 1280, "y": 110, "size": 36, "bold": True, "visible": True},
  "ram_used": {"x": 1280, "y": 200, "size": 36, "bold": True, "visible": True},
  "vram_used": {"x": 1490, "y": 200, "size": 36, "bold": True, "visible": True},
  "net_down": {"x": 1280, "y": 290, "size": 36, "bold": True, "visible": True},
  "net_up": {"x": 1490, "y": 290, "size": 36, "bold": True, "visible": True},
  "sys_title": {"x": 1620, "y": 110, "size": 36, "bold": True, "visible": True},
  "sys_time": {"x": 1620, "y": 200, "size": 36, "bold": True, "visible": True},
  "sys_date": {"x": 1620, "y": 250, "size": 36, "bold": True, "visible": True},
  "sys_volume": {"x": 1620, "y": 350, "size": 36, "bold": True, "visible": True, "text": "VOL "},
  "sys_disk": {"x": 1830, "y": 215, "size": 36, "bold": True, "visible": True},
  "sys_disk2": {"x": 1620, "y": 290, "size": 36, "bold": True, "visible": True},
  "sys_disk3": {"x": 1830, "y": 290, "size": 36, "bold": True, "visible": True},
  "cpu_bar": {"x": 560, "y": 240, "size": 24, "bold": True, "visible": False},
  "gpu_bar": {"x": 960, "y": 240, "size": 24, "bold": True, "visible": False},
  "ram_bar": {"x": 1280, "y": 240, "size": 24, "bold": True, "visible": False},
  "vram_bar": {"x": 1490, "y": 240, "size": 24, "bold": True, "visible": False},
  "sys_disk_bar": {"x": 1830, "y": 245, "size": 24, "bold": True, "visible": False},
  "sys_disk2_bar": {"x": 1620, "y": 320, "size": 24, "bold": True, "visible": False},
  "sys_disk3_bar": {"x": 1830, "y": 320, "size": 24, "bold": True, "visible": False},
  "sys_disk_free": {"x": 1830, "y": 260, "size": 24, "bold": False, "visible": False},
  "sys_disk2_free": {"x": 1620, "y": 335, "size": 24, "bold": False, "visible": False},
  "sys_disk3_free": {"x": 1830, "y": 335, "size": 24, "bold": False, "visible": False},
  "ram_free_bar": {"x": 1280, "y": 280, "size": 24, "bold": True, "visible": False},
  "ram_temp": {"x": 1280, "y": 320, "size": 24, "bold": False, "visible": False},
  "nvme_temp": {"x": 1830, "y": 370, "size": 24, "bold": False, "visible": False}
}

ELEMENT_DESCRIPTIONS = {
    "fps_title": ("FPS Title", "Título de FPS (ej. 'FPS')"),
    "fps_val": ("FPS Value", "Valor de FPS en tiempo real (ej. '180')"),
    "fps_ms": ("Frame Time", "Tiempo de renderizado de frame en ms (ej. '5.5ms')"),
    "cpu_title": ("CPU Title", "Título de sección CPU (ej. 'CPU')"),
    "cpu_val": ("CPU Load Text", "Texto con porcentaje de carga de CPU (ej. '45%')"),
    "cpu_bar": ("CPU Load Bar", "Barra gráfica de progreso de carga de CPU"),
    "cpu_temp": ("CPU Temp", "Temperatura del procesador en °C (ej. '65°C')"),
    "cpu_power": ("CPU Power", "Consumo de energía de CPU en Watts (W) (ej. '35W')"),
    "cpu_mhz": ("CPU Frequency", "Frecuencia de reloj del procesador en MHz (ej. '4200MHz')"),
    "gpu_title": ("GPU Title", "Título de sección GPU (ej. 'GPU')"),
    "gpu_val": ("GPU Load Text", "Texto con porcentaje de carga de GPU (ej. '78%')"),
    "gpu_bar": ("GPU Load Bar", "Barra gráfica de progreso de carga de GPU"),
    "gpu_temp": ("GPU Temp", "Temperatura de la tarjeta de video en °C (ej. '62°C')"),
    "gpu_power": ("GPU Power", "Consumo de energía de GPU en Watts (W) (ej. '180W')"),
    "gpu_mhz": ("GPU Frequency", "Frecuencia de reloj de GPU en MHz (ej. '1950MHz')"),
    "gpu_volt_fan": ("GPU Volt/Fan", "Voltaje y RPM de ventilador de GPU (ej. '1.05V 2100RPM')"),
    "mem_title": ("Memory Title", "Título de sección Memoria (ej. 'MEMORY')"),
    "ram_used": ("RAM Used Text", "Texto con consumo de RAM (ej. '7.5G' o '7.5G/16G')"),
    "ram_bar": ("RAM Used Bar", "Barra gráfica de progreso de consumo de memoria RAM"),
    "vram_used": ("VRAM Used Text", "Texto con consumo de VRAM (ej. '4.2G' o '4.2G/8G')"),
    "vram_bar": ("VRAM Used Bar", "Barra gráfica de progreso de consumo de memoria VRAM"),
    "net_down": ("Net Download", "Velocidad de descarga de red (ej. '240 KB/s')"),
    "net_up": ("Net Upload", "Velocidad de subida de red (ej. '45 KB/s')"),
    "sys_title": ("System Title", "Título de sección Sistema (ej. 'SYSTEM')"),
    "sys_time": ("System Time", "Hora en tiempo real del sistema (HH:MM:SS)"),
    "sys_date": ("System Date", "Fecha en tiempo real del sistema (dd/MM/yyyy)"),
    "sys_volume": ("System Volume", "Volumen y estado de audio del sistema (ej. 'VOL 55%')"),
    "sys_disk": ("Disk 1 Text", "Texto con espacio de Disco 1 (ej. 'Root 35%' o '120G/500G')"),
    "sys_disk_bar": ("Disk 1 Bar", "Barra gráfica de progreso de espacio de Disco 1"),
    "sys_disk2": ("Disk 2 Text", "Texto con espacio de Disco 2 (ej. 'Games 50%' o '250G/500G')"),
    "sys_disk2_bar": ("Disk 2 Bar", "Barra gráfica de progreso de espacio de Disco 2"),
    "sys_disk3": ("Disk 3 Text", "Texto con espacio de Disco 3 (ej. 'Docs 65%' o '370G/1000G')"),
    "sys_disk3_bar": ("Disk 3 Bar", "Barra gráfica de progreso de espacio de Disco 3"),
    "sys_disk_free": ("Disk 1 Free", "Texto con espacio libre de Disco 1 (ej. 'Root Free 380G')"),
    "sys_disk2_free": ("Disk 2 Free", "Texto con espacio libre de Disco 2 (ej. 'Games Free 250G')"),
    "sys_disk3_free": ("Disk 3 Free", "Texto con espacio libre de Disco 3 (ej. 'Docs Free 630G')"),
    "ram_free_bar": ("RAM Free Bar", "Barra gráfica de progreso de memoria RAM libre"),
    "ram_temp": ("RAM Temp", "Temperatura de memoria RAM en °C (ej. 'RAM Temp: 38°C')"),
    "nvme_temp": ("NVMe Temp", "Temperatura del disco NVMe principal en °C (ej. 'NVMe Temp: 45°C')"),
}

SCALE = 0.5
WIDTH, HEIGHT = int(1920 * SCALE), int(480 * SCALE)

class LayoutEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Turing Smart Screen 8.8\" Layout & Properties Editor")
        self.root.configure(bg="#0f0f13")
        self.root.geometry(f"{WIDTH + 340}x{HEIGHT + 450}")
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
        self.selected_key = None
        self.selected_keys = []
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Build Sidebar Controls in Right Frame
        self.sel_title_lbl = tk.Label(right_frame, text="Selected: None", fg="#ffffff", 
                                      bg="#161622", font=("Helvetica", 11, "bold"))
        self.sel_title_lbl.pack(pady=8)

        # Custom Label Text Frame (Only shown for static _title keys)
        self.text_frame = tk.Frame(right_frame, bg="#161622")
        tk.Label(self.text_frame, text="Custom Label Text:", fg="#a0a0aa", bg="#161622", font=("Helvetica", 9)).pack(anchor=tk.W, pady=2)
        self.text_var = tk.StringVar()
        self.text_entry = tk.Entry(self.text_frame, textvariable=self.text_var, bg="#1e1e24", fg="#ffffff", 
                                   insertbackground="#ffffff", bd=0, highlightthickness=1, highlightbackground="#252538", 
                                   highlightcolor="#00b4ff", font=("Helvetica", 10, "bold"))
        self.text_entry.pack(fill=tk.X, pady=4)
        self.text_var.trace_add("write", lambda *args: self.update_selected_text())
        self.updating_sidebar = False

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

        # Display Format Dropdown
        self.render_type_frame = tk.Frame(right_frame, bg="#161622")
        tk.Label(self.render_type_frame, text="Display Format:", fg="#a0a0aa", bg="#161622", font=("Helvetica", 9)).pack(anchor=tk.W, pady=2)
        self.render_type_var = tk.StringVar(value="Standard")
        self.render_type_menu = tk.OptionMenu(self.render_type_frame, self.render_type_var, *["Standard", "Detailed", "Chart"],
                                               command=lambda e: self.update_selected_property())
        self.render_type_menu.configure(bg="#1e1e24", fg="#ffffff", activebackground="#2b2b36", activeforeground="#ffffff", 
                                         highlightthickness=0, bd=0, font=("Helvetica", 9, "bold"))
        self.render_type_menu["menu"].configure(bg="#161622", fg="#ffffff", activebackground="#00b4ff", activeforeground="#ffffff")
        self.render_type_menu.pack(fill=tk.X, pady=4)

        # Separator & Background Settings
        tk.Frame(right_frame, height=1, bg="#252538").pack(fill=tk.X, pady=12)
        tk.Label(right_frame, text="Background Mode:", fg="#00b4ff", bg="#161622", font=("Helvetica", 9, "bold")).pack(anchor=tk.W, pady=2)
        
        self.bg_mode_var = tk.StringVar(value="video")
        self.bg_mode_menu = tk.OptionMenu(right_frame, self.bg_mode_var, *["video", "image"], command=self.update_global_config)
        self.bg_mode_menu.configure(bg="#1e1e24", fg="#ffffff", activebackground="#2b2b36", activeforeground="#ffffff", 
                                     highlightthickness=0, bd=0, font=("Helvetica", 9, "bold"))
        self.bg_mode_menu["menu"].configure(bg="#161622", fg="#ffffff", activebackground="#00b4ff", activeforeground="#ffffff")
        self.bg_mode_menu.pack(fill=tk.X, pady=5)

        self.choose_img_btn = tk.Button(right_frame, text="Choose Image...", command=self.choose_background_image,
                                        fg="#ffffff", bg="#252538", activeforeground="#ffffff", 
                                        activebackground="#2b2b46", bd=0, padx=10, pady=4, 
                                        font=("Helvetica", 9, "bold"))
        self.choose_img_btn.pack(fill=tk.X, pady=5)

        self.img_path_lbl = tk.Label(right_frame, text="No image selected", fg="#a0a0aa", bg="#161622", 
                                     font=("Helvetica", 8), wraplength=140, justify=tk.LEFT)
        self.img_path_lbl.pack(fill=tk.X, pady=2)

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

        # Bottom Scrollable Available Elements Manager
        self.create_elements_manager(left_frame)

    def load_layout(self):
        try:
            if os.path.exists(LAYOUT_FILE):
                with open(LAYOUT_FILE) as f:
                    self.layout = json.load(f)
                    # Automatically migrate gpu_power_desc to gpu_volt_fan if gpu_power_desc exists
                    if "gpu_power_desc" in self.layout:
                        if "gpu_volt_fan" not in self.layout or self.layout["gpu_volt_fan"].get("x") == 960:
                            self.layout["gpu_volt_fan"] = self.layout["gpu_power_desc"].copy()
                            self.layout["gpu_volt_fan"]["x"] = 1190
                            self.layout["gpu_volt_fan"]["y"] = 210
                        del self.layout["gpu_power_desc"]

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
                        elif k != "config" and "font" not in self.layout[k]:
                            self.layout[k]["font"] = "DejaVuSans"
                    
                    if "config" not in self.layout:
                        self.layout["config"] = {"mode": "video", "image_path": ""}
                    return
        except Exception as e:
            messagebox.showwarning("Error Loading Layout", f"Could not load layout.json, using defaults.\n{e}")
        self.layout = DEFAULT_LAYOUT.copy()

    def draw_elements(self):
        self.canvas.delete("draggable")
        
        # Load and draw background image if image mode is active
        self.canvas.delete("bg_image")
        cfg = self.layout.get("config", {"mode": "video", "image_path": ""})
        if cfg.get("mode", "video") == "image" and cfg.get("image_path", ""):
            bg_path = cfg.get("image_path", "")
            if os.path.exists(bg_path):
                try:
                    pil_img = Image.open(bg_path).convert("RGBA").resize((WIDTH, HEIGHT))
                    self.bg_photo = ImageTk.PhotoImage(pil_img)
                    self.canvas.create_image(0, 0, image=self.bg_photo, anchor=tk.NW, tags="bg_image")
                    self.canvas.tag_lower("bg_image")
                except Exception as e:
                    print(f"Error loading background image: {e}")

        display_texts = {
            "fps_title": self.layout.get("fps_title", {}).get("text", "FPS"), 
            "fps_val": "0", 
            "fps_ms": "0.0ms",
            "cpu_title": self.layout.get("cpu_title", {}).get("text", "CPU"), 
            "cpu_val": "45%", 
            "cpu_temp": "55°C",
            "cpu_power": "42W", 
            "cpu_mhz": "4200MHz",
            "gpu_title": self.layout.get("gpu_title", {}).get("text", "GPU"), 
            "gpu_val": "78%", 
            "gpu_temp": "62°C",
            "gpu_power": "180W", 
            "gpu_mhz": "1950MHz", 
            "gpu_volt_fan": "1.05V 2100RPM",
            "mem_title": self.layout.get("mem_title", {}).get("text", "MEMORY"), 
            "ram_used": f"{self.layout.get('ram_used', {}).get('text', 'RAM ')}7.5G/16G" if self.layout.get("ram_used", {}).get("render_type", "text") == "graph" else f"{self.layout.get('ram_used', {}).get('text', 'RAM ')}7.5G", 
            "vram_used": f"{self.layout.get('vram_used', {}).get('text', 'VRAM ')}4.2G/8G" if self.layout.get("vram_used", {}).get("render_type", "text") == "graph" else f"{self.layout.get('vram_used', {}).get('text', 'VRAM ')}4.2G", 
            "net_down": f"{self.layout.get('net_down', {}).get('text', 'DOWN ↓')}240 KB/s",
            "net_up": f"{self.layout.get('net_up', {}).get('text', 'UP ↑')}45 KB/s",
            "sys_title": self.layout.get("sys_title", {}).get("text", "SYSTEM"), 
            "sys_time": "12:34:56", 
            "sys_date": "18/05/2026",
            "sys_volume": f"{self.layout.get('sys_volume', {}).get('text', 'VOL ')}55%",
            "sys_disk": f"{self.layout.get('sys_disk', {}).get('text', 'DISK1 ')}120G/500G" if self.layout.get("sys_disk", {}).get("render_type", "text") == "graph" else f"{self.layout.get('sys_disk', {}).get('text', 'DISK1 ')}35%",
            "sys_disk2": f"{self.layout.get('sys_disk2', {}).get('text', 'DISK2 ')}250G/500G" if self.layout.get("sys_disk2", {}).get("render_type", "text") == "graph" else f"{self.layout.get('sys_disk2', {}).get('text', 'DISK2 ')}50%",
            "sys_disk3": f"{self.layout.get('sys_disk3', {}).get('text', 'DISK3 ')}370G/1000G" if self.layout.get("sys_disk3", {}).get("render_type", "text") == "graph" else f"{self.layout.get('sys_disk3', {}).get('text', 'DISK3 ')}65%",
            "sys_disk_free": f"{self.layout.get('sys_disk_free', {}).get('text', 'Root Free ')}380G",
            "sys_disk2_free": f"{self.layout.get('sys_disk2_free', {}).get('text', 'Games Free ')}250G",
            "sys_disk3_free": f"{self.layout.get('sys_disk3_free', {}).get('text', 'Docs Free ')}630G",
            "ram_temp": f"{self.layout.get('ram_temp', {}).get('text', 'RAM Temp: ')}38°C",
            "nvme_temp": f"{self.layout.get('nvme_temp', {}).get('text', 'NVMe Temp: ')}45°C"
        }
        
        colors = {
            "fps_title": "#00b4ff", "cpu_title": "#00b4ff", "gpu_title": "#00b4ff",
            "mem_title": "#00b4ff", "sys_title": "#00b4ff", "fps_val": "#00ff66", "sys_time": "#ffffff", "sys_date": "#ffffff", "sys_volume": "#ffffff"
        }

        font_family_map = {
            "DejaVuSans": "DejaVu Sans",
            "DejaVuSerif": "DejaVu Serif",
            "LiberationSans": "Liberation Sans",
            "LiberationMono": "Liberation Mono",
            "Ubuntu": "Ubuntu",
            "Roboto": "Roboto"
        }
        self.canvas_items = {}
        for key, prop in self.layout.items():
            if key == "config":
                continue
            visible = prop.get("visible", True)
            if not visible:
                continue
            x = int(prop.get("x", 0) * SCALE)
            y = int(prop.get("y", 0) * SCALE)
            size = int(prop.get("size", 36) * SCALE)
            bold = prop.get("bold", True)
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
                elif key in ["cpu_power", "gpu_power", "cpu_mhz", "gpu_mhz"]:
                    color = "#a0a0aa"
            else:
                color = "#454552" # Dark, semi-transparent grey for hidden/disabled elements

            graph_compatible = ["cpu_val", "gpu_val", "ram_used", "vram_used", "sys_disk", "sys_disk2", "sys_disk3"]
            if key in graph_compatible and prop.get("render_type") == "chart":
                bar_h = int(size * 2.2)
                bar_w = int(size * 5)
                
                # Chart theme colors based on key
                if "cpu" in key:
                    fill_color = "#30100c" if visible else "#1c0b08"
                    line_color = "#ff4b28" if visible else "#802514"
                elif "gpu" in key:
                    fill_color = "#0c2a16" if visible else "#06170c"
                    line_color = "#28d25a" if visible else "#14692d"
                elif "ram" in key or "vram" in key:
                    fill_color = "#0c2230" if visible else "#06121a"
                    line_color = "#00b4ff" if visible else "#005a80"
                else:
                    fill_color = "#200c2a" if visible else "#100615"
                    line_color = "#be2dff" if visible else "#5f1680"
                    
                # Background chart box
                bg_item = self.canvas.create_rectangle(
                    x, y, x + bar_w, y + bar_h,
                    fill="#0a0c12" if visible else "#06070a",
                    outline=line_color,
                    width=1, tags=("draggable", key)
                )
                
                # Faint grid lines mock
                self.canvas.create_line(
                    x + 1, y + bar_h // 2, x + bar_w - 1, y + bar_h // 2,
                    fill="#1b2838", dash=(2, 2), tags=("draggable", key)
                )
                self.canvas.create_line(
                    x + 1, y + bar_h // 4, x + bar_w - 1, y + bar_h // 4,
                    fill="#121a24", dash=(1, 2), tags=("draggable", key)
                )
                self.canvas.create_line(
                    x + 1, y + (3 * bar_h) // 4, x + bar_w - 1, y + (3 * bar_h) // 4,
                    fill="#121a24", dash=(1, 2), tags=("draggable", key)
                )
                
                # Mock line chart coordinates (smooth rolling hills)
                mock_vals = [20, 35, 25, 55, 40, 75, 65, 85, 70, 90]
                mock_points = []
                for idx, val in enumerate(mock_vals):
                    px = x + 2 + idx * ((bar_w - 4) / (len(mock_vals) - 1))
                    py = y + bar_h - 2 - (val / 100.0) * (bar_h - 4)
                    mock_points.append((px, py))
                
                # Draw area fill mock
                poly_points = [(mock_points[0][0], y + bar_h - 2)] + mock_points + [(mock_points[-1][0], y + bar_h - 2)]
                self.canvas.create_polygon(
                    poly_points, fill=fill_color,
                    tags=("draggable", key)
                )
                
                # Draw chart line mock
                self.canvas.create_line(
                    mock_points, fill=line_color,
                    width=2, tags=("draggable", key)
                )
                
                # Draw live ticker dot
                dot_x, dot_y = mock_points[-1]
                self.canvas.create_oval(
                    dot_x - 3, dot_y - 3,
                    dot_x + 3, dot_y + 3,
                    fill=line_color, outline="#ffffff", tags=("draggable", key)
                )
                
                # Small label text
                lbl_text = key.replace("_used", "").replace("_val", "").upper()
                if "disk" in lbl_text.lower():
                    lbl_text = "DISK"
                self.canvas.create_text(
                    x + 4, y + 4, text=lbl_text,
                    fill="#8888aa" if visible else "#454552",
                    font=("Helvetica", int(14 * SCALE), "normal"),
                    anchor=tk.NW, tags=("draggable", key)
                )
                
                # Small value mock text
                val_text = "47%"
                if "ram" in key or "vram" in key:
                    val_text = "7.5G" if key == "ram_used" else "4.2G"
                elif "disk" in key:
                    val_text = "35%"
                self.canvas.create_text(
                    x + bar_w - 4, y + 4, text=val_text,
                    fill="#ffffff" if visible else "#454552",
                    font=("Helvetica", int(14 * SCALE), "bold"),
                    anchor=tk.NE, tags=("draggable", key)
                )
                
                self.canvas_items[key] = bg_item
                item = bg_item
            elif key.endswith("_bar"):
                bar_h = int(size)
                bar_w = int(size * 5)
                # Background progress bar
                bg_item = self.canvas.create_rectangle(
                    x, y, x + bar_w, y + bar_h,
                    fill="#1f1f2e" if visible else "#16161c",
                    outline="#505064" if visible else "#2a2a35",
                    width=2, tags=("draggable", key)
                )
                # Filled bar mock (e.g. 60% load)
                fill_color = "#00ff66" if visible else "#1b4d32"
                fg_item = self.canvas.create_rectangle(
                    x + 2, y + 2, x + int(bar_w * 0.60) - 2, y + bar_h - 2,
                    fill=fill_color, outline="",
                    tags=("draggable", key)
                )
                # Small helper label above the bar
                lbl_txt = key.replace("_bar", "").upper() + " BAR"
                lbl_color = "#8888aa" if visible else "#454552"
                self.canvas.create_text(
                    x, y - 14,
                    text=lbl_txt, fill=lbl_color,
                    font=("Helvetica", 8, "normal"),
                    anchor=tk.NW, tags=("draggable", key)
                )
                self.canvas_items[key] = bg_item
                item = bg_item
            else:
                # Create text canvas item
                item = self.canvas.create_text(
                    x, y, text=txt, fill=color, 
                    font=(font_family, size, font_weight), 
                    anchor=tk.NW, tags=("draggable", key)
                )
                self.canvas_items[key] = item

            # Bind mouse and click events
            self.canvas.tag_bind(item, "<Button-1>", lambda event, k=key, i=item: self.start_drag(event, k, i))
            self.canvas.tag_bind(item, "<B1-Motion>", self.drag)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self.stop_drag)
            self.canvas.tag_bind(item, "<Double-Button-1>", lambda event, k=key: self.on_double_click(k))

        # Draw a tiny neon indicator if this is the selected element
        if hasattr(self, "selected_keys") and self.selected_keys:
            for k in self.selected_keys:
                if k in self.canvas_items:
                    bbox = self.canvas.bbox(self.canvas_items[k])
                    if bbox:
                        self.canvas.create_rectangle(
                            bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, 
                            outline="#00b4ff", width=1, tags=("draggable", "selection_box")
                        )

    def start_drag(self, event, key, item):
        shift_held = bool(event.state & 0x0001)
        if not hasattr(self, "selected_keys"):
            self.selected_keys = []
            
        if shift_held:
            if key not in self.selected_keys:
                self.selected_keys.append(key)
        else:
            if key not in self.selected_keys:
                self.selected_keys = [key]
                
        self.selected_key = key
        self.drag_item = item
        self.drag_key = key
        
        # Store original layout coordinates of all selected keys
        self.drag_start_coords = {}
        for k in self.selected_keys:
            self.drag_start_coords[k] = (self.layout[k]["x"], self.layout[k]["y"])
            
        self.drag_start_mouse = (event.x, event.y)
        self.update_sidebar()
        
        # Redraw only selection boxes to preserve active item bindings
        self.canvas.delete("selection_box")
        for k in self.selected_keys:
            if k in self.canvas_items:
                bbox = self.canvas.bbox(self.canvas_items[k])
                if bbox:
                    self.canvas.create_rectangle(
                        bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, 
                        outline="#00b4ff", width=1, tags=("draggable", "selection_box")
                    )
        return "break"

    def drag(self, event):
        if self.drag_item:
            dx = int((event.x - self.drag_start_mouse[0]) / SCALE)
            dy = int((event.y - self.drag_start_mouse[1]) / SCALE)
            
            # Move all selected elements together by the offset
            for k in self.selected_keys:
                orig_x, orig_y = self.drag_start_coords[k]
                new_x = max(0, min(orig_x + dx, 1920 - 50))
                new_y = max(0, min(orig_y + dy, 480 - 20))
                self.layout[k]["x"] = new_x
                self.layout[k]["y"] = new_y
                
                # Update coordinates instantly on canvas
                if k in self.canvas_items:
                    item_type = self.canvas.type(self.canvas_items[k])
                    if item_type == "rectangle":
                        nx = int(new_x * SCALE)
                        ny = int(new_y * SCALE)
                        prop = self.layout[k]
                        size = int(prop.get("size", 36) * SCALE)
                        bar_h = int(size)
                        bar_w = int(size * 5)
                        self.canvas.coords(self.canvas_items[k], nx, ny, nx + bar_w, ny + bar_h)
                        # Also update foreground filled rectangles dynamically!
                        for item in self.canvas.find_withtag(k):
                            if item != self.canvas_items[k]:
                                self.canvas.coords(item, nx + 2, ny + 2, nx + int(bar_w * 0.60) - 2, ny + bar_h - 2)
                    else:
                        self.canvas.coords(self.canvas_items[k], new_x * SCALE, new_y * SCALE)
                    
            # Redraw only selection boxes instantly
            self.canvas.delete("selection_box")
            for k in self.selected_keys:
                if k in self.canvas_items:
                    bbox = self.canvas.bbox(self.canvas_items[k])
                    if bbox:
                        self.canvas.create_rectangle(
                            bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, 
                            outline="#00b4ff", width=1, tags=("draggable", "selection_box")
                        )

    def stop_drag(self, event):
        if self.drag_item:
            self.drag_item = None
            self.save_layout()
            self.draw_elements()

    def on_canvas_click(self, event):
        clicked_item = self.canvas.find_withtag(tk.CURRENT)
        if not clicked_item or "draggable" not in self.canvas.gettags(clicked_item[0]):
            self.selected_keys = []
            self.selected_key = None
            self.update_sidebar()
            self.draw_elements()

    def on_double_click(self, key):
        editable_keys = ["fps_title", "cpu_title", "gpu_title", "mem_title", "sys_title", "ram_used", "vram_used", "sys_disk", "sys_disk2", "sys_disk3", "net_down", "net_up", "sys_volume", "sys_disk_free", "sys_disk2_free", "sys_disk3_free", "ram_temp", "nvme_temp"]
        if key in editable_keys:
            from tkinter import simpledialog
            curr_text = self.layout[key].get("text", self.get_default_title(key))
            new_text = simpledialog.askstring("Edit Text", f"Edit custom text for {key}:", initialvalue=curr_text)
            if new_text is not None:
                self.layout[key]["text"] = new_text
                self.save_layout()
                self.draw_elements()
                self.update_sidebar()
        else:
            self.toggle_visibility(key)

    def toggle_visibility(self, key):
        self.layout[key]["visible"] = not self.layout[key]["visible"]
        if self.selected_key == key:
            self.vis_var.set(self.layout[key]["visible"])
        self.save_layout()
        self.draw_elements()

    def update_sidebar(self):
        self.updating_sidebar = True
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
            
            # Show render type dropdown for graph-compatible keys
            graph_compatible = ["cpu_val", "gpu_val", "ram_used", "vram_used", "sys_disk", "sys_disk2", "sys_disk3"]
            if self.selected_key in graph_compatible:
                self.render_type_frame.pack(fill=tk.X, pady=8, after=self.font_menu)
                rt = prop.get("render_type", "text")
                if rt == "chart":
                    self.render_type_var.set("Chart")
                elif rt == "graph":
                    self.render_type_var.set("Detailed")
                else:
                    self.render_type_var.set("Standard")
                self.render_type_menu.configure(state=tk.NORMAL)
            else:
                self.render_type_frame.pack_forget()
            
            editable_keys = ["fps_title", "cpu_title", "gpu_title", "mem_title", "sys_title", "ram_used", "vram_used", "sys_disk", "sys_disk2", "sys_disk3", "net_down", "net_up", "sys_volume", "sys_disk_free", "sys_disk2_free", "sys_disk3_free", "ram_temp", "nvme_temp"]
            if self.selected_key in editable_keys:
                if self.selected_key in graph_compatible:
                    self.text_frame.pack(fill=tk.X, pady=8, after=self.render_type_frame)
                else:
                    self.text_frame.pack(fill=tk.X, pady=8, after=self.font_menu)
                self.text_var.set(prop.get("text", self.get_default_title(self.selected_key)))
            else:
                self.text_frame.pack_forget()
        else:
            self.sel_title_lbl.configure(text="Selected: None", fg="#a0a0aa")
            self.vis_chk.configure(state=tk.DISABLED)
            self.size_scale.configure(state=tk.DISABLED)
            self.bold_chk.configure(state=tk.DISABLED)
            self.font_menu.configure(state=tk.DISABLED)
            self.render_type_frame.pack_forget()
            self.text_frame.pack_forget()

        # Update background settings fields from layout global config
        cfg = self.layout.get("config", {"mode": "video", "image_path": ""})
        bg_mode = cfg.get("mode", "video")
        self.bg_mode_var.set(bg_mode)
        img_path = cfg.get("image_path", "")
        if img_path:
            self.img_path_lbl.configure(text=os.path.basename(img_path))
        else:
            self.img_path_lbl.configure(text="No image selected")
            
        if bg_mode == "video":
            self.choose_img_btn.configure(state=tk.DISABLED)
        else:
            self.choose_img_btn.configure(state=tk.NORMAL)
        self.updating_sidebar = False

    def update_selected_text(self):
        if getattr(self, "updating_sidebar", False):
            return
        editable_keys = ["fps_title", "cpu_title", "gpu_title", "mem_title", "sys_title", "ram_used", "vram_used", "sys_disk", "sys_disk2", "sys_disk3", "net_down", "net_up", "sys_volume", "sys_disk_free", "sys_disk2_free", "sys_disk3_free", "ram_temp", "nvme_temp"]
        if self.selected_key and self.selected_key in editable_keys:
            self.layout[self.selected_key]["text"] = self.text_var.get()
            self.save_layout()
            self.draw_elements()

    def get_default_title(self, key):
        defaults = {
            "fps_title": "FPS",
            "cpu_title": "CPU",
            "gpu_title": "GPU",
            "mem_title": "MEMORY",
            "sys_title": "SYSTEM",
            "ram_used": "RAM ",
            "vram_used": "VRAM ",
            "sys_disk": "DISK1 ",
            "sys_disk2": "DISK2 ",
            "sys_disk3": "DISK3 ",
            "net_down": "DOWN ↓",
            "net_up": "UP ↑",
            "sys_volume": "VOL ",
            "sys_disk_free": "Root Free ",
            "sys_disk2_free": "Games Free ",
            "sys_disk3_free": "Docs Free ",
            "ram_temp": "RAM Temp: ",
            "nvme_temp": "NVMe Temp: "
        }
        return defaults.get(key, "")

    def update_selected_property(self):
        if getattr(self, "updating_sidebar", False):
            return
        if self.selected_key:
            self.layout[self.selected_key]["visible"] = self.vis_var.get()
            self.layout[self.selected_key]["size"] = self.size_scale.get()
            self.layout[self.selected_key]["bold"] = self.bold_var.get()
            self.layout[self.selected_key]["font"] = self.font_var.get()
            
            # Save render_type if compatible
            graph_compatible = ["cpu_val", "gpu_val", "ram_used", "vram_used", "sys_disk", "sys_disk2", "sys_disk3"]
            if self.selected_key in graph_compatible:
                rt_val = self.render_type_var.get()
                if rt_val == "Chart":
                    self.layout[self.selected_key]["render_type"] = "chart"
                elif rt_val == "Detailed":
                    self.layout[self.selected_key]["render_type"] = "graph"
                else:
                    self.layout[self.selected_key]["render_type"] = "text"
                
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
            self.layout = {k: v.copy() for k, v in DEFAULT_LAYOUT.items()}
            self.selected_key = None
            self.update_sidebar()
            self.draw_elements()
            self.save_layout()

    def choose_background_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            if "config" not in self.layout:
                self.layout["config"] = {"mode": "video", "image_path": ""}
            self.layout["config"]["image_path"] = file_path
            self.layout["config"]["mode"] = "image"
            self.bg_mode_var.set("image")
            self.choose_img_btn.configure(state=tk.NORMAL)
            self.img_path_lbl.configure(text=os.path.basename(file_path))
            self.save_layout()
            self.draw_elements()
            messagebox.showinfo("Background Mode Changed", "Please restart the Turing Dashboard service in the Control Center to apply the changes (Stop -> Start).")

    def update_global_config(self, val=None):
        if "config" not in self.layout:
            self.layout["config"] = {"mode": "video", "image_path": ""}
        bg_mode = self.bg_mode_var.get()
        self.layout["config"]["mode"] = bg_mode
        if bg_mode == "video":
            self.choose_img_btn.configure(state=tk.DISABLED)
        else:
            self.choose_img_btn.configure(state=tk.NORMAL)
        self.save_layout()
        self.draw_elements()
        messagebox.showinfo("Background Mode Changed", "Please restart the Turing Dashboard service in the Control Center to apply the changes (Stop -> Start).")

    def create_elements_manager(self, parent):
        bottom_frame = tk.LabelFrame(parent, text=" 🎨 AVAILABLE ELEMENTS MANAGER (ADD / REMOVE TELEMETRY) ", fg="#00b4ff", 
                                      bg="#161622", bd=1, padx=10, pady=5, 
                                      font=("Helvetica", 10, "bold"))
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        container = tk.Frame(bottom_frame, bg="#161622")
        container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(container, bg="#161622", height=150, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="#161622")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mouse wheel for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.refresh_elements_manager()

    def refresh_elements_manager(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        tk.Label(self.scrollable_frame, text="ELEMENT NAME", fg="#00b4ff", bg="#161622", 
                 font=("Helvetica", 9, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Label(self.scrollable_frame, text="STATUS", fg="#00b4ff", bg="#161622", 
                 font=("Helvetica", 9, "bold")).grid(row=0, column=1, sticky="w", padx=10, pady=5)
        tk.Label(self.scrollable_frame, text="DESCRIPTION", fg="#00b4ff", bg="#161622", 
                 font=("Helvetica", 9, "bold")).grid(row=0, column=2, sticky="w", padx=10, pady=5)
        tk.Label(self.scrollable_frame, text="ACTION", fg="#00b4ff", bg="#161622", 
                 font=("Helvetica", 9, "bold")).grid(row=0, column=3, sticky="w", padx=10, pady=5)
                 
        tk.Frame(self.scrollable_frame, height=1, bg="#252538").grid(row=1, column=0, columnspan=4, sticky="ew", pady=3)
        
        row_idx = 2
        for key in sorted(ELEMENT_DESCRIPTIONS.keys()):
            friendly_name, desc = ELEMENT_DESCRIPTIONS[key]
            prop = self.layout.get(key, {})
            visible = prop.get("visible", False)
            
            tk.Label(self.scrollable_frame, text=f"{friendly_name} ({key})", fg="#ffffff", bg="#161622",
                     font=("Helvetica", 9, "bold")).grid(row=row_idx, column=0, sticky="w", padx=10, pady=5)
                     
            status_text = "● ADDED" if visible else "○ REMOVED"
            status_color = "#00ff66" if visible else "#ff3333"
            tk.Label(self.scrollable_frame, text=status_text, fg=status_color, bg="#161622",
                     font=("Helvetica", 9, "bold")).grid(row=row_idx, column=1, sticky="w", padx=10, pady=5)
                     
            tk.Label(self.scrollable_frame, text=desc, fg="#a0a0aa", bg="#161622",
                     font=("Helvetica", 9)).grid(row=row_idx, column=2, sticky="w", padx=10, pady=5)
                     
            btn_text = "Remove" if visible else "Add"
            btn_bg = "#ff3333" if visible else "#00b4ff"
            
            btn = tk.Button(self.scrollable_frame, text=btn_text, bg=btn_bg, fg="#ffffff",
                            activebackground="#ffffff", activeforeground=btn_bg, bd=0, padx=8, pady=2,
                            font=("Helvetica", 8, "bold"),
                            command=lambda k=key, v=visible: self.toggle_element_manager(k, v))
            btn.grid(row=row_idx, column=3, sticky="w", padx=10, pady=5)
            
            row_idx += 1

    def toggle_element_manager(self, key, current_visible):
        prop = self.layout.setdefault(key, {})
        prop["visible"] = not current_visible
        
        if prop["visible"]:
            if prop.get("x", 0) == 0 and prop.get("y", 0) == 0:
                default_item = DEFAULT_LAYOUT.get(key, {"x": 50, "y": 50, "size": 36, "bold": True})
                prop["x"] = default_item.get("x", 50)
                prop["y"] = default_item.get("y", 50)
                prop["size"] = default_item.get("size", 36)
                prop["bold"] = default_item.get("bold", True)
                prop["font"] = default_item.get("font", "DejaVuSans")
            self.selected_key = key
        else:
            if self.selected_key == key:
                self.selected_key = None
                
        self.save_layout()
        self.draw_elements()
        self.update_sidebar()
        self.refresh_elements_manager()

if __name__ == "__main__":
    root = tk.Tk()
    app = LayoutEditor(root)
    root.mainloop()
