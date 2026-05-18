#!/usr/bin/env python3
"""Turing 8.8" — Video + Live Telemetry. Usage: python3 turing_dashboard.py"""
import serial, time, os, json, signal, sys, numpy as np
import builtins
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    builtins.print(*args, **kwargs)
from PIL import Image, ImageDraw, ImageFont
from library.lcd.serialize import image_to_BGRA, chunked

VIDEO_PATH = "/mnt/UDISK/video/DeskDisplay2.mp4.mp4"
from library.lcd.lcd_comm_rev_c import LcdCommRevC
def get_com_port():
    from serial.tools.list_ports import comports
    # 1. First priority: exact g_serial USB gadget d port (0x0525/0xa4a7) which is ACM1
    for p in comports():
        if p.vid == 0x0525 and p.pid == 0xa4a7:
            try:
                LcdCommRevC._wake_up_device(p)
            except: pass
            print(f"🔌 Auto-detected screen by gadget VID/PID: {p.device}")
            return p.device
            
    # 2. Second priority: general auto-detect
    try:
        detected = LcdCommRevC.auto_detect_com_port()
        if detected:
            print(f"🔌 Auto-detected screen: {detected}")
            return detected
    except Exception as e:
        print(f"⚠️ Port auto-detection failed: {e}")
        
    return "/dev/ttyACM1"

COM_PORT = get_com_port()
DW, DH = 480, 1920
BRIGHTNESS = 0x8c
GREEN = (0, 200, 0)
MANGOHUD_JSON = "/tmp/mangohud_stats.json"
UPDATE_SEC = 0.1

LAYOUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "layout.json")
DEFAULT_LAYOUT = {
  "config": {"mode": "video", "image_path": ""},
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

def load_layout():
    try:
        if os.path.exists(LAYOUT_FILE):
            with open(LAYOUT_FILE) as f:
                ly = json.load(f)
                if "gpu_power_desc" in ly:
                    if "gpu_volt_fan" not in ly or ly["gpu_volt_fan"].get("x") == 960:
                        ly["gpu_volt_fan"] = ly["gpu_power_desc"].copy()
                        ly["gpu_volt_fan"]["x"] = 1190
                        ly["gpu_volt_fan"]["y"] = 210
                    del ly["gpu_power_desc"]
                return ly
    except:
        pass
    return DEFAULT_LAYOUT

running = True
HISTORIES = {}
signal.signal(signal.SIGINT, lambda s,f: globals().update(running=False))
signal.signal(signal.SIGTERM, lambda s,f: globals().update(running=False))

def _f(font_name, b, sz):
    font_files = {
        "DejaVuSans": ("DejaVuSans-Bold", "DejaVuSans"),
        "DejaVuSerif": ("DejaVuSerif-Bold", "DejaVuSerif"),
        "LiberationSans": ("LiberationSans-Bold", "LiberationSans-Regular"),
        "LiberationMono": ("LiberationMono-Bold", "LiberationMono-Regular"),
        "Ubuntu": ("Ubuntu-B", "Ubuntu-R"),
        "Roboto": ("Roboto-Bold", "Roboto-Regular")
    }
    bold_file, reg_file = font_files.get(font_name, ("DejaVuSans-Bold", "DejaVuSans"))
    target_name = bold_file if b else reg_file
    
    search_paths = [
        f"/usr/share/fonts/truetype/dejavu/{target_name}.ttf",
        f"/usr/share/fonts/TTF/{target_name}.ttf",
        f"/usr/share/fonts/truetype/liberation/{target_name}.ttf",
        f"/usr/share/fonts/liberation/{target_name}.ttf",
        f"/usr/share/fonts/truetype/ubuntu/{target_name}.ttf",
        f"/usr/share/fonts/ubuntu/{target_name}.ttf",
        f"/usr/share/fonts/truetype/roboto/{target_name}.ttf",
        f"/usr/share/fonts/roboto/{target_name}.ttf",
    ]
    for path in search_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, sz)
            except:
                pass
    try:
        for root, dirs, files in os.walk("/usr/share/fonts"):
            for file in files:
                if file.lower() == f"{target_name.lower()}.ttf":
                    try:
                        return ImageFont.truetype(os.path.join(root, file), sz)
                    except:
                        pass
    except:
        pass
    return ImageFont.load_default()

FONT_CACHE = {}
def get_cached_font(font_name, size, bold):
    key = (font_name, size, bold)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = _f(font_name, bold, size)
    return FONT_CACHE[key]

def spad(s,d):
    r=len(d)%250
    if r: d+=bytearray(250-r)
    s.write(d); s.flush()

def image_to_BGRA(img):
    arr = np.array(img.convert('RGBA'))
    mask = (arr[:, :, 0] == 0) & (arr[:, :, 1] == 200) & (arr[:, :, 2] == 0)
    bgra = np.empty_like(arr)
    bgra[:, :, 0] = arr[:, :, 2] # B
    bgra[:, :, 1] = arr[:, :, 1] # G
    bgra[:, :, 2] = arr[:, :, 0] # R
    bgra[:, :, 3] = 255          # A
    bgra[mask] = [0, 0, 0, 0]
    return bgra.tobytes(), 4

def send_full(s,img):
    img=img.rotate(180,expand=True)
    bgra,_=image_to_BGRA(img)
    fd=b'\x00'.join(chunked(bgra,249))
    spad(s,bytearray([0x86,0xef,0x69,0x00,0x00,0x00,0x01]));time.sleep(0.01)
    s.write(bytearray([0x2c]*250));s.flush();time.sleep(0.01)
    dc=bytearray([0xc8,0xef,0x69,0x00,0x38,0x40])+int(DW*DW/64).to_bytes(2,"big")
    spad(s,dc);time.sleep(0.01)
    spad(s,bytearray(fd))
    
    t0_read = time.time()
    resp = b""
    while b'full_png_sucess' not in resp and (time.time() - t0_read) < 5.0:
        if s.in_waiting > 0:
            resp += s.read(s.in_waiting)
        else:
            time.sleep(0.005)
            
    spad(s,bytearray([0xcf,0xef,0x69,0x00,0x00,0x00,0x01]))
    time.sleep(0.01);s.read(s.in_waiting)
    return resp

def read_gpu_mhz():
    try:
        with open("/sys/class/hwmon/hwmon2/device/pp_dpm_sclk") as f:
            for l in f:
                if "*" in l:
                    p = l.split()
                    for item in p:
                        if "mhz" in item.lower():
                            return int(item.lower().replace("mhz", ""))
    except: pass
    return 0

def read_gpu():
    r={"load":0,"temp":0,"power":0,"volt":0,"fan":0,"mhz":0,"vram_total":0.0,"vram_used":0.0}
    for k,p in [("load","/sys/class/hwmon/hwmon2/device/gpu_busy_percent"),
                ("temp","/sys/class/hwmon/hwmon2/temp1_input"),
                ("power","/sys/class/hwmon/hwmon2/power1_average"),
                ("volt","/sys/class/hwmon/hwmon2/in0_input"),
                ("fan","/sys/class/hwmon/hwmon2/fan1_input")]:
        try:
            with open(p) as f: v=int(f.read().strip())
            if k=="temp": v=v//1000
            elif k=="power": v=v//1000000
            elif k=="volt": v=v/1000
            r[k]=v
        except: pass
    try:
        with open("/sys/class/hwmon/hwmon2/device/mem_info_vram_total") as f:
            r["vram_total"] = int(f.read().strip()) / (1024.0 * 1024.0 * 1024.0)
    except: pass
    try:
        with open("/sys/class/hwmon/hwmon2/device/mem_info_vram_used") as f:
            r["vram_used"] = int(f.read().strip()) / (1024.0 * 1024.0 * 1024.0)
    except: pass
    r["mhz"] = read_gpu_mhz()
    return r

def read_ram_temp():
    # Look for jc42, ee1004, spd5 or similar hwmon names
    for hwmon in os.listdir("/sys/class/hwmon") if os.path.exists("/sys/class/hwmon") else []:
        try:
            name_path = os.path.join("/sys/class/hwmon", hwmon, "name")
            if os.path.exists(name_path):
                with open(name_path) as f:
                    name = f.read().strip()
                if name in ["jc42", "spd5", "ee1004"]:
                    temp_path = os.path.join("/sys/class/hwmon", hwmon, "temp1_input")
                    if os.path.exists(temp_path):
                        with open(temp_path) as f:
                            temp_val = float(f.read().strip()) / 1000.0
                            return f"{temp_val:.0f}°C"
        except:
            pass
    return "N/A"

def read_nvme_temp():
    root_nvme = None
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "/":
                    dev = parts[0]
                    if "nvme" in dev:
                        idx = dev.find("nvme")
                        if idx != -1:
                            part = dev[idx:]
                            num_str = ""
                            for char in part[4:]:
                                if char.isdigit():
                                    num_str += char
                                else:
                                    break
                            root_nvme = "nvme" + num_str
                            break
    except:
        pass

    first_nvme_hwmon = None
    target_hwmon = None
    
    for hwmon in os.listdir("/sys/class/hwmon") if os.path.exists("/sys/class/hwmon") else []:
        try:
            name_path = os.path.join("/sys/class/hwmon", hwmon, "name")
            if os.path.exists(name_path):
                with open(name_path) as f:
                    name = f.read().strip()
                if name == "nvme":
                    if not first_nvme_hwmon:
                        first_nvme_hwmon = hwmon
                    if root_nvme:
                        dev_path = os.path.realpath(os.path.join("/sys/class/hwmon", hwmon, "device"))
                        if root_nvme in dev_path:
                            target_hwmon = hwmon
                            break
        except:
            pass

    hwmon_to_read = target_hwmon if target_hwmon else first_nvme_hwmon
    if hwmon_to_read:
        try:
            temp_path = os.path.join("/sys/class/hwmon", hwmon_to_read, "temp1_input")
            if os.path.exists(temp_path):
                with open(temp_path) as f:
                    temp_val = float(f.read().strip()) / 1000.0
                    return f"{temp_val:.0f}°C"
        except:
            pass
    return "N/A"

prev_cpu_energy = [0, 0.0]
def read_cpu_power(cpu_l):
    global prev_cpu_energy
    try:
        with open("/sys/class/powercap/intel-rapl:0/energy_uj") as f:
            energy = int(f.read().strip())
        now = time.time()
        power = 0.0
        if prev_cpu_energy[0] > 0 and now > prev_cpu_energy[1]:
            dt = now - prev_cpu_energy[1]
            if dt > 0.05:
                diff = energy - prev_cpu_energy[0]
                if diff >= 0:
                    power = (diff / 1000000.0) / dt
        prev_cpu_energy = [energy, now]
        if 1.0 <= power <= 500.0:
            return int(power)
    except:
        pass
    return int(15 + (cpu_l * 0.6))

def read_ct():
    for p in ["/sys/class/hwmon/hwmon0/temp1_input","/sys/class/hwmon/hwmon1/temp1_input"]:
        try:
            with open(p) as f: v=int(f.read().strip()); return v//1000 if v>1000 else v
        except: pass
    return 0

def read_ram():
    try:
        with open('/proc/meminfo') as f:
            i={}
            for l in f: p=l.split(); i[p[0].rstrip(':')]=int(p[1])
            return (i['MemTotal']-i['MemAvailable'])/(1024*1024), i['MemTotal']/(1024*1024)
    except: return 0,0

def read_mh():
    if not os.path.exists(MANGOHUD_JSON): return None
    try:
        if (time.time()-os.path.getmtime(MANGOHUD_JSON))>5: return None
        with open(MANGOHUD_JSON) as f: return json.load(f)
    except: return None

prev_net=[0,0,0]
def read_net():
    try:
        with open('/sys/class/net/enp10s0/statistics/rx_bytes') as f: rx=int(f.read().strip())
        with open('/sys/class/net/enp10s0/statistics/tx_bytes') as f: tx=int(f.read().strip())
        return rx,tx
    except: return 0,0

def read_volume():
    try:
        import subprocess
        out = subprocess.check_output(["pamixer", "--get-volume-human"], stderr=subprocess.DEVNULL).decode().strip()
        return out
    except:
        return "N/A"

W=(255,255,255)

def read_disks():
    disks = [] # list of (mountpoint, percent, used_gb, total_gb)
    import psutil
    try:
        parts = psutil.disk_partitions(all=False)
        seen_devices = set()
        seen_mounts = set()
        # 1. Root '/' first
        for p in parts:
            if p.mountpoint == '/':
                try:
                    usage = psutil.disk_usage('/')
                    used_gb = usage.used / (1024.0 * 1024.0 * 1024.0)
                    total_gb = usage.total / (1024.0 * 1024.0 * 1024.0)
                    disks.append(('/', usage.percent, used_gb, total_gb))
                    seen_devices.add(p.device)
                    seen_mounts.add('/')
                except: pass
                break
        
        # 2. Other physical mount points
        for p in parts:
            if p.mountpoint in seen_mounts or p.device in seen_devices or 'loop' in p.device or 'ram' in p.device:
                continue
            if p.mountpoint.startswith('/boot') or p.mountpoint.startswith('/efi'):
                continue
            if not p.fstype or p.fstype in ('tmpfs', 'devtmpfs', 'overlay', 'squashfs'):
                continue
            try:
                usage = psutil.disk_usage(p.mountpoint)
                used_gb = usage.used / (1024.0 * 1024.0 * 1024.0)
                total_gb = usage.total / (1024.0 * 1024.0 * 1024.0)
                disks.append((p.mountpoint, usage.percent, used_gb, total_gb))
                seen_devices.add(p.device)
                seen_mounts.add(p.mountpoint)
            except: pass
            if len(disks) >= 3:
                break
    except: pass
    
    # Pad to 3 disks if needed
    while len(disks) < 3:
        try:
            usage = psutil.disk_usage('/')
            used_gb = usage.used / (1024.0 * 1024.0 * 1024.0)
            total_gb = usage.total / (1024.0 * 1024.0 * 1024.0)
            disks.append(('/', usage.percent, used_gb, total_gb))
        except:
            disks.append(('/', 0.0, 0.0, 0.0))
            
    return disks

def build():
    global prev_net
    # Load layout and global config
    ly = load_layout()
    cfg = ly.get("config", {"mode": "video", "image_path": ""})
    bg_mode = cfg.get("mode", "video")
    bg_path = cfg.get("image_path", "")
    
    if bg_mode == "image" and bg_path and os.path.exists(bg_path):
        try:
            img = Image.open(bg_path).convert('RGB').resize((1920, 480))
        except:
            img = Image.new('RGB', (1920, 480), (0, 0, 0))
    else:
        img = Image.new('RGB', (1920, 480), GREEN)
        
    d = ImageDraw.Draw(img)
    gpu=read_gpu(); ct=read_ct(); ru,rt=read_ram(); mh=read_mh()
    rx,tx=read_net(); now=time.time()
    
    if prev_net[2]>0:
        dt=max(now-prev_net[2],0.1); dl=(rx-prev_net[0])/dt/1024; ul=(tx-prev_net[1])/dt/1024
    else: dl=ul=0
    prev_net=[rx,tx,now]; gm=mh is not None
    
    disk_data = read_disks()
    dp1_lbl, dp1, dp1_used, dp1_total = disk_data[0]
    dp2_lbl, dp2, dp2_used, dp2_total = disk_data[1]
    dp3_lbl, dp3, dp3_used, dp3_total = disk_data[2]
    
    try:
        import psutil
        cpu_l = psutil.cpu_percent()
        cpu_mhz = int(psutil.cpu_freq().current)
    except: cpu_l, cpu_mhz = 0, 0
    cpu_p = read_cpu_power(cpu_l)

    # Core percentages for chart rolling histories
    cpu_pct = float(mh.get('cpu_load', cpu_l) if gm else cpu_l)
    gpu_pct = float(mh.get('gpu_load', gpu['load']) if gm else gpu['load'])
    
    ram_total_calc = rt if rt > 0 else 16.0
    ram_u_calc = mh.get('ram_used', ru) if gm else ru
    ram_pct = (ram_u_calc / ram_total_calc) * 100.0 if ram_total_calc > 0 else 0.0
    
    vram_total_calc = mh.get('gpu_vram_total', 0.0) if gm else 0.0
    if not vram_total_calc:
        vram_total_calc = gpu['vram_total']
    vram_u_calc = mh.get('gpu_vram_used', 0.0) if gm else 0.0
    if not vram_u_calc:
        vram_u_calc = gpu['vram_used']
    vram_pct = (vram_u_calc / vram_total_calc) * 100.0 if vram_total_calc > 0 else 0.0
    
    # Load layout
    ly = load_layout()

    def draw_chart(key, val_str, x, y, size, visible):
        if not visible:
            return
            
        pct = 0.0
        if key == "cpu_val":
            pct = cpu_pct
        elif key == "gpu_val":
            pct = gpu_pct
        elif key == "ram_used":
            pct = ram_pct
        elif key == "vram_used":
            pct = vram_pct
        elif key == "sys_disk":
            pct = dp1
        elif key == "sys_disk2":
            pct = dp2
        elif key == "sys_disk3":
            pct = dp3
            
        # Append to global history
        hist = HISTORIES.setdefault(key, [])
        hist.append(pct)
        max_len = 50
        if len(hist) > max_len:
            hist.pop(0)
            
        # Chart dimensions
        width = int(size * 5)
        height = int(size * 2.2)
        
        # Background rectangle
        d.rectangle([x, y, x + width, y + height], fill=(10, 12, 18), outline=(45, 50, 68), width=2)
        
        # Grid lines (50% and 25%/75%)
        d.line([x + 2, y + height // 2, x + width - 2, y + height // 2], fill=(30, 35, 48), width=1)
        d.line([x + 2, y + height // 4, x + width - 2, y + height // 4], fill=(20, 24, 32), width=1)
        d.line([x + 2, y + (3 * height) // 4, x + width - 2, y + (3 * height) // 4], fill=(20, 24, 32), width=1)
        
        # Map values to points
        num_points = len(hist)
        if num_points > 1:
            points = []
            for i, val in enumerate(hist):
                idx_from_right = num_points - 1 - i
                px = x + width - 4 - idx_from_right * ((width - 6) / (max_len - 1))
                if px < x + 4:
                    continue
                py = y + height - 4 - (val / 100.0) * (height - 8)
                points.append((px, py))
                
            # Theme Colors based on key
            if "cpu" in key:
                fill_color = (48, 16, 12)
                line_color = (255, 75, 40)
                dot_color = (255, 130, 90)
            elif "gpu" in key:
                fill_color = (12, 42, 22)
                line_color = (40, 210, 90)
                dot_color = (110, 255, 140)
            elif "ram" in key or "vram" in key:
                fill_color = (12, 34, 48)
                line_color = (0, 180, 255)
                dot_color = (100, 220, 255)
            else:
                fill_color = (32, 12, 42)
                line_color = (190, 45, 255)
                dot_color = (230, 100, 255)
                
            if len(points) > 1:
                poly_points = [(points[0][0], y + height - 4)] + points + [(points[-1][0], y + height - 4)]
                d.polygon(poly_points, fill=fill_color)
                d.line(points, fill=line_color, width=2)
                
                latest_x, latest_y = points[-1]
                d.ellipse([latest_x - 3, latest_y - 3, latest_x + 3, latest_y + 3], fill=dot_color, outline=(255, 255, 255))
                
        # Draw label and value
        lbl = key.replace("_used", "").replace("_val", "").upper()
        if "disk" in lbl.lower():
            lbl = "DISK"
            
        font_sm = get_cached_font("DejaVuSans", 11, False)
        font_sm_bold = get_cached_font("DejaVuSans", 11, True)
        
        d.text((x + 6, y + 6), lbl, fill=(160, 165, 180), font=font_sm)
        
        # Calculate current value text
        clean_val = val_str
        for prefix in ["RAM ", "VRAM ", "VOL ", disk_prefix, disk2_prefix, disk3_prefix]:
            if clean_val.startswith(prefix):
                clean_val = clean_val[len(prefix):]
                break
                
        def get_text_w(t, f):
            try: return f.getlength(t)
            except:
                try: return f.getsize(t)[0]
                except: return len(t) * 7
                
        tw = get_text_w(clean_val, font_sm_bold)
        d.text((x + width - 6 - tw, y + 6), clean_val, fill=(255, 255, 255), font=font_sm_bold)

    def draw_text(key, val_str):
        item = ly.get(key, DEFAULT_LAYOUT.get(key, {"x": 0, "y": 0, "size": 36, "bold": True, "visible": True, "font": "DejaVuSans"}))
        if isinstance(item, list):
            x, y = item[0], item[1]
            size, bold, visible = 36, True, True
            font_name = "DejaVuSans"
            r_type = "text"
        else:
            x = item.get("x", 0)
            y = item.get("y", 0)
            size = item.get("size", 36)
            bold = item.get("bold", True)
            visible = item.get("visible", True)
            font_name = item.get("font", "DejaVuSans")
            r_type = item.get("render_type", "text")
            
        if r_type == "chart":
            draw_chart(key, val_str, x, y, size, visible)
            return
            
        if visible:
            font = get_cached_font(font_name, size, bold)
            d.text((x, y), str(val_str), fill=W, font=font)

    def draw_bar(key, pct):
        item = ly.get(key, DEFAULT_LAYOUT.get(key, {"x": 0, "y": 0, "size": 24, "bold": True, "visible": False}))
        if isinstance(item, list):
            x, y = item[0], item[1]
            size, visible = 24, False
        else:
            x = item.get("x", 0)
            y = item.get("y", 0)
            size = item.get("size", 24)
            visible = item.get("visible", False)
        if visible:
            pct = max(0.0, min(100.0, pct))
            bar_h = int(size)
            bar_w = int(size * 5)
            
            # Draw background rectangle
            d.rectangle([x, y, x + bar_w, y + bar_h], fill=(30, 30, 40), outline=(80, 80, 100), width=2)
            
            # Dynamic color representation
            if pct < 60:
                bar_color = (0, 255, 100)
            elif pct < 85:
                bar_color = (255, 204, 0)
            else:
                bar_color = (255, 51, 51)
                
            if pct > 0:
                fill_w = int(bar_w * (pct / 100.0))
                x0 = x + 2
                x1 = max(x0, x + fill_w - 2)
                y0 = y + 2
                y1 = max(y0, y + bar_h - 2)
                d.rectangle([x0, y0, x1, y1], fill=bar_color)
    
    # Row 0: Titles
    fps_title_txt = ly.get("fps_title", {}).get("text", "FPS")
    cpu_title_txt = ly.get("cpu_title", {}).get("text", "CPU")
    gpu_title_txt = ly.get("gpu_title", {}).get("text", "GPU")
    mem_title_txt = ly.get("mem_title", {}).get("text", "MEMORY")
    sys_title_txt = ly.get("sys_title", {}).get("text", "SYSTEM")

    ram_prefix = ly.get("ram_used", {}).get("text", "RAM ")
    vram_prefix = ly.get("vram_used", {}).get("text", "VRAM ")
    ram_temp_prefix = ly.get("ram_temp", {}).get("text", "RAM Temp: ")
    nvme_temp_prefix = ly.get("nvme_temp", {}).get("text", "NVMe Temp: ")
    def get_disk_label(key, mountpoint):
        disk_prop = ly.get(key, {})
        if "text" not in disk_prop:
            # User has not customized this label yet - dynamically show the volume name
            if mountpoint == '/':
                return "Root "
            else:
                base = os.path.basename(mountpoint.rstrip('/')).strip()
                if not base and mountpoint.startswith('/run/media/'):
                    parts = mountpoint.split('/')
                    if len(parts) > 4:
                        base = parts[-1]
                return base + " " if base else "Disk "
        # User has customized this label - return their customized text (even if empty)
        return disk_prop.get("text", "")

    disk_prefix = get_disk_label("sys_disk", dp1_lbl)
    disk2_prefix = get_disk_label("sys_disk2", dp2_lbl)
    disk3_prefix = get_disk_label("sys_disk3", dp3_lbl)
    net_down_prefix = ly.get("net_down", {}).get("text", "DOWN ↓")
    net_up_prefix = ly.get("net_up", {}).get("text", "UP ↑")
    vol_prefix = ly.get("sys_volume", {}).get("text", "VOL ")

    if gm:
        fps=int(mh.get("fps",0))
        draw_text("fps_title", fps_title_txt)
        draw_text("fps_val", f"{fps}")
        draw_text("fps_ms", f"{mh.get('frametime',0):.1f}ms")
    else:
        draw_text("fps_title", fps_title_txt)
        draw_text("fps_val", "180")
        draw_text("fps_ms", "1.0ms")
    draw_text("cpu_title", cpu_title_txt)
    draw_text("gpu_title", gpu_title_txt)
    draw_text("mem_title", mem_title_txt)
    draw_text("sys_title", sys_title_txt)
    
    # Row 1: Main values
    if gm:
        draw_text("cpu_val", f"{mh.get('cpu_load',cpu_l):.0f}%")
        draw_text("cpu_temp", f"{int(mh.get('cpu_temp',ct))}°C")
        draw_text("gpu_val", f"{mh.get('gpu_load',gpu['load']):.0f}%")
        draw_text("gpu_temp", f"{int(mh.get('gpu_temp',gpu['temp']))}°C")
    else:
        draw_text("cpu_val", f"{cpu_l:.0f}%")
        draw_text("cpu_temp", f"{ct}°C")
        draw_text("gpu_val", f"{gpu['load']}%")
        draw_text("gpu_temp", f"{gpu['temp']}°C")

    # Format RAM used based on display format (render_type == graph means full)
    ram_rt = ly.get("ram_used", {}).get("render_type", "text")
    if ram_rt == "graph":
        ram_val_str = f"{ram_prefix}{mh.get('ram_used', ru):.1f}/{rt:.0f}G" if gm else f"{ram_prefix}{ru:.1f}/{rt:.0f}G"
    else:
        ram_val_str = f"{ram_prefix}{mh.get('ram_used', ru):.1f}G" if gm else f"{ram_prefix}{ru:.1f}G"
    draw_text("ram_used", ram_val_str)
    draw_text("ram_temp", f"{ram_temp_prefix}{read_ram_temp()}")
    draw_text("nvme_temp", f"{nvme_temp_prefix}{read_nvme_temp()}")

    # Format VRAM used based on display format (render_type == graph means full)
    vram_rt = ly.get("vram_used", {}).get("render_type", "text")
    vr = mh.get('gpu_vram_used', 0) if gm else 0
    if not vr:
        vr = gpu['vram_used']
    vrt = mh.get('gpu_vram_total', 0) if gm else 0
    if not vrt:
        vrt = gpu['vram_total']
        
    if vrt > 0:
        if vram_rt == "graph":
            vram_val_str = f"{vram_prefix}{vr:.1f}/{vrt:.0f}G"
        else:
            vram_val_str = f"{vram_prefix}{vr:.1f}G"
        draw_text("vram_used", vram_val_str)
        
    draw_text("sys_time", time.strftime("%H:%M:%S"))
    draw_text("sys_date", time.strftime("%d/%m/%Y"))
    draw_text("sys_volume", f"{vol_prefix}{read_volume()}")
    
    def get_disk_val_str(key, prefix, used, total, pct):
        r_type = ly.get(key, {}).get("render_type", "text")
        if r_type == "graph":
            if total >= 950.0:
                return f"{prefix}{used/1024.0:.1f}T/{total/1024.0:.1f}T"
            else:
                if total >= 100.0:
                    return f"{prefix}{used:.0f}G/{total:.0f}G"
                else:
                    return f"{prefix}{used:.1f}G/{total:.1f}G"
        else:
            return f"{prefix}{pct:.0f}%"

    draw_text("sys_disk", get_disk_val_str("sys_disk", disk_prefix, dp1_used, dp1_total, dp1))
    draw_text("sys_disk2", get_disk_val_str("sys_disk2", disk2_prefix, dp2_used, dp2_total, dp2))
    draw_text("sys_disk3", get_disk_val_str("sys_disk3", disk3_prefix, dp3_used, dp3_total, dp3))

    # Draw 3 new disk free space labels
    disk_free_prefix = ly.get("sys_disk_free", {}).get("text", "Root Free ")
    disk2_free_prefix = ly.get("sys_disk2_free", {}).get("text", "Games Free ")
    disk3_free_prefix = ly.get("sys_disk3_free", {}).get("text", "Docs Free ")
    
    def get_disk_free_val_str(key, prefix, used, total):
        free = max(0.0, total - used)
        if total >= 950.0:
            return f"{prefix}{free/1024.0:.1f}T"
        else:
            if total >= 100.0:
                return f"{prefix}{free:.0f}G"
            else:
                return f"{prefix}{free:.1f}G"

    draw_text("sys_disk_free", get_disk_free_val_str("sys_disk_free", disk_free_prefix, dp1_used, dp1_total))
    draw_text("sys_disk2_free", get_disk_free_val_str("sys_disk2_free", disk2_free_prefix, dp2_used, dp2_total))
    draw_text("sys_disk3_free", get_disk_free_val_str("sys_disk3_free", disk3_free_prefix, dp3_used, dp3_total))

    # Draw progress bars
    draw_bar("cpu_bar", float(mh.get('cpu_load', cpu_l) if gm else cpu_l))
    draw_bar("gpu_bar", float(mh.get('gpu_load', gpu['load']) if gm else gpu['load']))
    
    ram_total = rt if rt > 0 else 16.0
    ram_u = mh.get('ram_used', ru) if gm else ru
    ram_used_pct = (ram_u / ram_total) * 100.0 if ram_total > 0 else 0.0
    
    draw_bar("ram_bar", ram_used_pct)
    # Draw RAM free graph/progress bar
    draw_bar("ram_free_bar", 100.0 - ram_used_pct)
    
    vram_total = mh.get('gpu_vram_total', 0.0) if gm else 0.0
    if not vram_total:
        vram_total = gpu['vram_total']
    vram_u = mh.get('gpu_vram_used', 0.0) if gm else 0.0
    if not vram_u:
        vram_u = gpu['vram_used']
    draw_bar("vram_bar", (vram_u / vram_total) * 100.0 if vram_total > 0 else 0.0)
    
    draw_bar("sys_disk_bar", dp1)
    draw_bar("sys_disk2_bar", dp2)
    draw_bar("sys_disk3_bar", dp3)
    
    # Row 2: Secondary
    if gm:
        draw_text("cpu_power", f"{int(mh.get('cpu_power',cpu_p))}W")
        cclk=mh.get('cpu_mhz',cpu_mhz)
        if cclk: draw_text("cpu_mhz", f"{int(cclk)}MHz")
        
        draw_text("gpu_power", f"{int(mh.get('gpu_power',gpu['power']))}W")
        gclk=mh.get('gpu_core_clock',gpu['mhz'])
        if gclk: draw_text("gpu_mhz", f"{int(gclk)}MHz")
    else:
        draw_text("cpu_power", f"{cpu_p}W")
        if cpu_mhz: draw_text("cpu_mhz", f"{cpu_mhz}MHz")
        
        draw_text("gpu_power", f"{gpu['power']}W")
        if gpu['mhz']: draw_text("gpu_mhz", f"{gpu['mhz']}MHz")

    # Draw GPU voltage/fan if visible/active
    draw_text("gpu_volt_fan", f"{gpu['volt']:.2f}V  Fan:{gpu['fan']}RPM")
        
    draw_text("net_down", f"{net_down_prefix}{dl:.0f} KB/s")
    draw_text("net_up", f"{net_up_prefix}{ul:.0f} KB/s")
    

    return img.rotate(90, expand=True)

def phase1():
    global COM_PORT
    print("📡 Phase 1: Video + overlay init...")
    rtscts_val = False if "ACM1" in COM_PORT else True
    s=serial.Serial(COM_PORT,115200,timeout=2,write_timeout=None,rtscts=rtscts_val)
    s.reset_input_buffer()
    s.reset_output_buffer()
    time.sleep(1) # Extra wait for port
    spad(s,bytearray([0x01,0xef,0x69,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0xc5,0xd3]))
    print("   Waiting for screen hardware reboot (3s)...")
    time.sleep(3); s.read(s.in_waiting) # EXTRA SAFE SLEEP FOR REBOOT
    
    ly = load_layout()
    cfg = ly.get("config", {"mode": "video", "image_path": ""})
    bg_mode = cfg.get("mode", "video")
    
    # 0x02 = STARTMODE_VIDEO, 0x01 = STARTMODE_IMAGE
    start_mode = 0x02 if bg_mode == "video" else 0x01
    
    # Wake up
    spad(s, bytearray([0x01,0xef,0x69,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0xc5,0xd3]))
    time.sleep(3); s.read(s.in_waiting)
        
    spad(s,bytearray([0x79,0xef,0x69,0x00,0x00,0x00,0x01]));time.sleep(0.5);s.read(s.in_waiting)
    spad(s,bytearray([0x96,0xef,0x69,0x00,0x00,0x00,0x01]));time.sleep(0.5);s.read(s.in_waiting)
    spad(s,bytearray([0x7b,0xef,0x69,0x00,0x00,0x00,0x01,0x00,0x00,0x00,BRIGHTNESS]));time.sleep(0.2)
    
    spad(s,bytearray([0x7d,0xef,0x69,0x00,0x00,0x00,0x05,0x00,0x00,0x00,0x2d,start_mode,0x00,0x01,0x00]));time.sleep(1)
    
    if bg_mode == "video":
        cmd=bytearray([0x78,0xef,0x69,0x00,0x00,0x00,len(VIDEO_PATH),0x00,0x00,0x00])+VIDEO_PATH.encode('ascii')
        spad(s,cmd);time.sleep(3);resp=s.read(s.in_waiting).strip(b'\x00') # SAFE SLEEP FOR VIDEO
        print(f"   Video: {'✅' if b'play_video_success' in resp else resp}")
    else:
        print("   Image Mode active. Bypassing hardware SD video command.")
        
    spad(s,bytearray([0xd0,0xef,0x69,0x00,0x00,0x00,0x01]));time.sleep(1);s.read(s.in_waiting)
    t=Image.new('RGB',(10,10),(255,0,0));bt,px=image_to_BGRA(t)
    for i in range(3):
        raw=bytearray()
        for l in range(10): raw+=(l*DW).to_bytes(3,"big")+(10).to_bytes(2,"big")+bt[l*10*px:(l+1)*10*px]
        isz=int(len(raw)+2).to_bytes(3,"big")
        pld=bytearray([0xcc,0xef,0x69,0x00])+isz+b'\x00'*3+i.to_bytes(4,'big')
        if len(raw)>250: raw=bytearray(b'\x00').join(chunked(bytes(raw),249))
        raw+=b'\xef\x69'
        spad(s,pld);spad(s,raw)
        spad(s,bytearray([0xcf,0xef,0x69,0x00,0x00,0x00,0x01]));time.sleep(0.2);s.read(s.in_waiting)
    s.close();print("   ✅ Ready!");time.sleep(2)
 
def main():
    global running
    print("╔═══════════════════════════════════════════╗")
    print("║  🎬 Turing 8.8\" Video+Telemetry Dashboard ║")
    print("║  Ctrl+C to stop                           ║")
    print("╚═══════════════════════════════════════════╝\n")
    phase1()
    print("\n📊 Live overlay (same serial session)...\n")
    rtscts_val = False if "ACM1" in COM_PORT else True
    s=serial.Serial(COM_PORT,115200,timeout=0.01,write_timeout=None,rtscts=rtscts_val)
    s.reset_input_buffer()
    s.reset_output_buffer()
    time.sleep(0.5)
    spad(s,bytearray([0x01,0xef,0x69,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0xc5,0xd3]))
    time.sleep(0.5);s.read(23)
    n=0
    while running:
        try:
            t0=time.time(); img=build(); resp=send_full(s,img); n+=1
            el=time.time()-t0
            mode="🎮" if read_mh() else "🖥️"
            print(f"   [{n}] {mode} {el:.1f}s {resp.decode(errors='ignore')}")
            end=time.time()+UPDATE_SEC
            while running and time.time()<end: time.sleep(0.05)
        except Exception as e:
            print(f"   ⚠️ Connection issue ({e}), reconnecting...");time.sleep(2)
            try: s.close()
            except: pass
            try:
                port = get_com_port()
                rtscts_val = False if "ACM1" in port else True
                s=serial.Serial(port,115200,timeout=0.01,write_timeout=None,rtscts=rtscts_val)
                s.reset_input_buffer()
                s.reset_output_buffer()
                time.sleep(0.5)
                spad(s,bytearray([0x01,0xef,0x69,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0xc5,0xd3]))
                time.sleep(0.5);s.read(23)
            except Exception as re:
                print(f"   ❌ Reconnect failed: {re}");time.sleep(2)
    try: s.close()
    except: pass
    print("\n✅ Stopped.")

if __name__=="__main__": main()
