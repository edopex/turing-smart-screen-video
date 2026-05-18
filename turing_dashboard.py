#!/usr/bin/env python3
"""Turing 8.8" — Video + Live Telemetry. Usage: python3 turing_dashboard.py"""
import serial, time, os, json, signal, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
from library.lcd.serialize import image_to_BGRA, chunked

VIDEO_PATH = "/mnt/UDISK/video/DeskDisplay2.mp4.mp4"
COM_PORT = "/dev/ttyACM1"
DW, DH = 480, 1920
BRIGHTNESS = 0x8c
GREEN = (0, 200, 0)
MANGOHUD_JSON = "/tmp/mangohud_stats.json"
UPDATE_SEC = 0.1

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

def load_layout():
    try:
        if os.path.exists(LAYOUT_FILE):
            with open(LAYOUT_FILE) as f:
                return json.load(f)
    except:
        pass
    return DEFAULT_LAYOUT

running = True
signal.signal(signal.SIGINT, lambda s,f: globals().update(running=False))
signal.signal(signal.SIGTERM, lambda s,f: globals().update(running=False))

def _f(b,sz):
    for d in ["TTF","truetype/dejavu"]:
        try: return ImageFont.truetype(f"/usr/share/fonts/{d}/{'DejaVuSans-Bold' if b else 'DejaVuSans'}.ttf",sz)
        except: pass
    return ImageFont.load_default()

FONT_CACHE = {}
def get_cached_font(size, bold):
    key = (size, bold)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = _f(bold, size)
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
    spad(s,bytearray([0xFF])+bytearray(fd))
    
    t0_read = time.time()
    resp = b""
    while b'full_png_sucess' not in resp and (time.time() - t0_read) < 1.0:
        chunk = s.read(1)
        if chunk:
            resp += chunk
        else:
            time.sleep(0.005)
            
    spad(s,bytearray([0xcf,0xef,0x69,0x00,0x00,0x00,0x01]))
    time.sleep(0.01);s.read(1024)
    return resp

def read_gpu():
    r={"load":0,"temp":0,"power":0,"volt":0,"fan":0}
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
    return r

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

W=(255,255,255)

def build():
    global prev_net
    # Draw in LANDSCAPE (1920x480)
    img=Image.new('RGB',(1920,480),GREEN); d=ImageDraw.Draw(img)
    gpu=read_gpu(); ct=read_ct(); ru,rt=read_ram(); mh=read_mh()
    rx,tx=read_net(); now=time.time()
    
    if prev_net[2]>0:
        dt=max(now-prev_net[2],0.1); dl=(rx-prev_net[0])/dt/1024; ul=(tx-prev_net[1])/dt/1024
    else: dl=ul=0
    prev_net=[rx,tx,now]; gm=mh is not None
    
    import shutil
    try:
        t, u, f = shutil.disk_usage("/")
        du_perc = u / t * 100
    except: du_perc = 0
    
    try:
        import psutil
        cpu_l = psutil.cpu_percent()
        cpu_mhz = int(psutil.cpu_freq().current)
    except: cpu_l, cpu_mhz = 0, 0
    
    # Load layout
    ly = load_layout()
    def draw_text(key, val_str):
        item = ly.get(key, DEFAULT_LAYOUT.get(key, {"x": 0, "y": 0, "size": 36, "bold": True, "visible": True}))
        if isinstance(item, list):
            x, y = item[0], item[1]
            size, bold, visible = 36, True, True
        else:
            x = item.get("x", 0)
            y = item.get("y", 0)
            size = item.get("size", 36)
            bold = item.get("bold", True)
            visible = item.get("visible", True)
        if visible:
            font = get_cached_font(size, bold)
            d.text((x, y), str(val_str), fill=W, font=font)
    
    # Row 0: Titles
    if gm:
        fps=int(mh.get("fps",0))
        draw_text("fps_title", "FPS")
        draw_text("fps_val", f"{fps}")
        draw_text("fps_ms", f"{mh.get('frametime',0):.1f}ms")
    else:
        draw_text("fps_title", "FPS")
        draw_text("fps_val", "180")
        draw_text("fps_ms", "5.5ms")
    draw_text("cpu_title", "CPU")
    draw_text("gpu_title", "GPU")
    draw_text("mem_title", "MEMORY")
    draw_text("sys_title", "SYSTEM")
    
    # Row 1: Main values
    if gm:
        draw_text("cpu_val", f"{mh.get('cpu_load',cpu_l):.0f}%")
        draw_text("cpu_temp", f"{int(mh.get('cpu_temp',ct))}°C")
        draw_text("gpu_val", f"{mh.get('gpu_load',gpu['load']):.0f}%")
        draw_text("gpu_temp", f"{int(mh.get('gpu_temp',gpu['temp']))}°C")
        draw_text("ram_used", f"RAM {mh.get('ram_used',ru):.1f}G")
        vr=mh.get('gpu_vram_used',0)
        if vr: draw_text("vram_used", f"VRAM {vr:.1f}G")
    else:
        draw_text("cpu_val", f"{cpu_l:.0f}%")
        draw_text("cpu_temp", f"{ct}°C")
        draw_text("gpu_val", f"{gpu['load']}%")
        draw_text("gpu_temp", f"{gpu['temp']}°C")
        draw_text("gpu_power_desc", f"{gpu['power']}W")
        draw_text("ram_used", f"RAM {ru:.1f}/{rt:.0f}G")
        
    draw_text("sys_time", time.strftime("%H:%M:%S"))
    draw_text("sys_disk", f"DISK {du_perc:.0f}%")
    
    # Row 2: Secondary
    if gm:
        draw_text("cpu_power", f"{int(mh.get('cpu_power',0))}W")
        cclk=mh.get('cpu_mhz',cpu_mhz)
        if cclk: draw_text("cpu_mhz", f"{int(cclk)}MHz")
        
        draw_text("gpu_power", f"{int(mh.get('gpu_power',gpu['power']))}W")
        gclk=mh.get('gpu_core_clock',0)
        if gclk: draw_text("gpu_mhz", f"{int(gclk)}MHz")
    else:
        if cpu_mhz: draw_text("cpu_power", f"{cpu_mhz}MHz")
        draw_text("gpu_power", f"{gpu['volt']:.2f}V  Fan:{gpu['fan']}RPM")
        
    draw_text("net_stat", f"NET ↓{dl:.0f} ↑{ul:.0f} KB/s")
    

    return img.rotate(90, expand=True)

def phase1():
    print("📡 Phase 1: Video + overlay init...")
    s=serial.Serial(COM_PORT,115200,timeout=2,write_timeout=2)
    time.sleep(1) # Extra wait for port
    spad(s,bytearray([0x01,0xef,0x69,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0xc5,0xd3]))
    print("   Waiting for screen hardware reboot (3s)...")
    time.sleep(3); s.read(1024) # EXTRA SAFE SLEEP FOR REBOOT
    
    spad(s,bytearray([0x79,0xef,0x69,0x00,0x00,0x00,0x01]));time.sleep(0.5);s.read(1024)
    spad(s,bytearray([0x96,0xef,0x69,0x00,0x00,0x00,0x01]));time.sleep(0.5);s.read(1024)
    spad(s,bytearray([0x7b,0xef,0x69,0x00,0x00,0x00,0x01,0x00,0x00,0x00,BRIGHTNESS]));time.sleep(0.2)
    spad(s,bytearray([0x7d,0xef,0x69,0x00,0x00,0x00,0x05,0x00,0x00,0x00,0x2d,0x02,0x00,0x01,0x00]));time.sleep(1)
    
    cmd=bytearray([0x78,0xef,0x69,0x00,0x00,0x00,len(VIDEO_PATH),0x00,0x00,0x00])+VIDEO_PATH.encode('ascii')
    spad(s,cmd);time.sleep(3);resp=s.read(1024).strip(b'\x00') # SAFE SLEEP FOR VIDEO
    print(f"   Video: {'✅' if b'play_video_success' in resp else resp}")
    
    spad(s,bytearray([0xd0,0xef,0x69,0x00,0x00,0x00,0x01]));time.sleep(1);s.read(1024)
    t=Image.new('RGB',(10,10),(255,0,0));bt,px=image_to_BGRA(t)
    for i in range(3):
        raw=bytearray()
        for l in range(10): raw+=(l*DW).to_bytes(3,"big")+(10).to_bytes(2,"big")+bt[l*10*px:(l+1)*10*px]
        isz=int(len(raw)+2).to_bytes(3,"big")
        pld=bytearray([0xcc,0xef,0x69,0x00])+isz+b'\x00'*3+i.to_bytes(4,'big')
        if len(raw)>250: raw=bytearray(b'\x00').join(chunked(bytes(raw),249))
        raw+=b'\xef\x69'
        spad(s,bytearray([0xFF])+pld);spad(s,bytearray([0xFF])+raw)
        spad(s,bytearray([0xcf,0xef,0x69,0x00,0x00,0x00,0x01]));time.sleep(0.2);s.read(1024)
    s.close();print("   ✅ Ready!");time.sleep(2)

def main():
    global running
    print("╔═══════════════════════════════════════════╗")
    print("║  🎬 Turing 8.8\" Video+Telemetry Dashboard ║")
    print("║  Ctrl+C to stop                           ║")
    print("╚═══════════════════════════════════════════╝\n")
    phase1()
    print("\n📊 Live overlay (same serial session)...\n")
    s=serial.Serial(COM_PORT,115200,timeout=0.01,write_timeout=2);time.sleep(0.5)
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
                s=serial.Serial(COM_PORT,115200,timeout=0.01,write_timeout=2);time.sleep(0.5)
                spad(s,bytearray([0x01,0xef,0x69,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0xc5,0xd3]))
                time.sleep(0.5);s.read(23)
            except Exception as re:
                print(f"   ❌ Reconnect failed: {re}");time.sleep(2)
    try: s.close()
    except: pass
    print("\n✅ Stopped.")

if __name__=="__main__": main()
