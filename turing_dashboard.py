#!/usr/bin/env python3
"""Turing 8.8" — Video + Live Telemetry. Usage: python3 turing_dashboard.py"""
import serial, time, os, json, signal, sys
from PIL import Image, ImageDraw, ImageFont
from library.lcd.serialize import image_to_BGRA, chunked

VIDEO_PATH = "/mnt/UDISK/video/DeskDisplay2.mp4.mp4"
COM_PORT = "/dev/ttyACM1"
DW, DH = 480, 1920
BRIGHTNESS = 0x8c
GREEN = (0, 200, 0)
MANGOHUD_JSON = "/tmp/mangohud_stats.json"
UPDATE_SEC = 3

running = True
signal.signal(signal.SIGINT, lambda s,f: globals().update(running=False))
signal.signal(signal.SIGTERM, lambda s,f: globals().update(running=False))

def _f(b,sz):
    for d in ["TTF","truetype/dejavu"]:
        try: return ImageFont.truetype(f"/usr/share/fonts/{d}/{'DejaVuSans-Bold' if b else 'DejaVuSans'}.ttf",sz)
        except: pass
    return ImageFont.load_default()
FT=_f(True,36); FV=_f(True,52); FL=_f(False,28); FS=_f(False,24)

def spad(s,d):
    r=len(d)%250
    if r: d+=bytearray(250-r)
    s.write(d); s.flush()

def image_to_BGRA(img):
    img=img.convert('RGBA'); bgra=bytearray()
    for y in range(img.height):
        for x in range(img.width):
            r,g,b,a=img.getpixel((x,y))
            if (r,g,b)==GREEN: bgra.extend([0,0,0,0])
            else: bgra.extend([b,g,r,255])
    return bytes(bgra),4

def send_full(s,img):
    img=img.rotate(180,expand=True)
    bgra,_=image_to_BGRA(img)
    fd=b'\x00'.join(chunked(bgra,249))
    spad(s,bytearray([0x86,0xef,0x69,0x00,0x00,0x00,0x01]));time.sleep(0.05)
    s.write(bytearray([0x2c]*250));s.flush();time.sleep(0.05)
    dc=bytearray([0xc8,0xef,0x69,0x00,0x38,0x40])+int(DW*DW/64).to_bytes(2,"big")
    spad(s,dc);time.sleep(0.05)
    spad(s,bytearray([0xFF])+bytearray(fd))
    time.sleep(0.5);resp=s.read(1024).strip(b'\x00')
    spad(s,bytearray([0xcf,0xef,0x69,0x00,0x00,0x00,0x01]))
    time.sleep(0.3);s.read(1024)
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

W=(255,255,255); G=(160,160,160); DG=(100,100,100); CT=(0,180,255)
def tc(t): return (100,200,255) if t<60 else (255,200,0) if t<80 else (255,80,80)
def fc(f): return (0,255,100) if f>=60 else (255,255,0) if f>=30 else (255,80,80)

# Se eliminó la versión "optimizada" de image_to_BGRA.
# La versión lenta de arriba actúa como un delay natural necesario.

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
    
    # Landscape layout: columns across 1920px, rows in 480px
    cols=[40, 440, 840, 1260, 1600]; y0=25; y1=85; y2=150
    
    # Row 0: Titles
    if gm:
        fps=int(mh.get("fps",0))
        d.text((cols[0],y0),"FPS",fill=CT,font=FT)
        d.text((cols[0]+90,y0-15),f"{fps}",fill=fc(fps),font=FV)
        d.text((cols[0]+230,y0+10),f"{mh.get('frametime',0):.1f}ms",fill=G,font=FL)
    else:
        d.text((cols[0],y0),"DESKTOP",fill=CT,font=FT)
    d.text((cols[1],y0),"CPU",fill=CT,font=FT)
    d.text((cols[2],y0),"GPU",fill=CT,font=FT)
    d.text((cols[3],y0),"MEMORY",fill=CT,font=FT)
    d.text((cols[4],y0),"SYSTEM",fill=CT,font=FT)
    
    # Row 1: Main values
    if gm:
        d.text((cols[1]+80,y1),f"{mh.get('cpu_load',cpu_l):.0f}%",fill=W,font=FV)
        d.text((cols[1]+220,y1+10),f"{int(mh.get('cpu_temp',ct))}°C",fill=tc(mh.get('cpu_temp',ct)),font=FL)
        d.text((cols[2]+80,y1),f"{mh.get('gpu_load',gpu['load']):.0f}%",fill=W,font=FV)
        d.text((cols[2]+220,y1+10),f"{int(mh.get('gpu_temp',gpu['temp']))}°C",fill=tc(mh.get('gpu_temp',gpu['temp'])),font=FL)
        d.text((cols[3],y1),f"RAM {mh.get('ram_used',ru):.1f}G",fill=W,font=FL)
        vr=mh.get('gpu_vram_used',0)
        if vr: d.text((cols[3]+210,y1),f"VRAM {vr:.1f}G",fill=(255,140,0),font=FL)
    else:
        d.text((cols[1]+80,y1),f"{cpu_l:.0f}%",fill=W,font=FV)
        d.text((cols[1]+220,y1+10),f"{ct}°C",fill=tc(ct),font=FL)
        d.text((cols[2]+80,y1),f"{gpu['load']}%",fill=W,font=FV)
        d.text((cols[2]+210,y1+10),f"{gpu['temp']}°C",fill=tc(gpu['temp']),font=FL)
        d.text((cols[2]+310,y1+10),f"{gpu['power']}W",fill=G,font=FL)
        d.text((cols[3],y1),f"RAM {ru:.1f}/{rt:.0f}G",fill=W,font=FL)
        
    d.text((cols[4],y1),time.strftime("%H:%M:%S"),fill=W,font=FV)
    d.text((cols[4]+210,y1+15),f"DISK {du_perc:.0f}%",fill=DG,font=FS)
    
    # Row 2: Secondary
    if gm:
        d.text((cols[1]+80,y2),f"{int(mh.get('cpu_power',0))}W",fill=G,font=FL)
        cclk=mh.get('cpu_mhz',cpu_mhz)
        if cclk: d.text((cols[1]+200,y2),f"{int(cclk)}MHz",fill=DG,font=FS)
        
        d.text((cols[2]+80,y2),f"{int(mh.get('gpu_power',gpu['power']))}W",fill=G,font=FL)
        gclk=mh.get('gpu_core_clock',0)
        if gclk: d.text((cols[2]+200,y2),f"{int(gclk)}MHz",fill=DG,font=FS)
    else:
        if cpu_mhz: d.text((cols[1]+80,y2),f"{cpu_mhz}MHz",fill=DG,font=FS)
        d.text((cols[2]+80,y2),f"{gpu['volt']:.2f}V  Fan:{gpu['fan']}RPM",fill=DG,font=FS)
        
    d.text((cols[3],y2),f"NET ↓{dl:.0f} ↑{ul:.0f} KB/s",fill=DG,font=FS)
    

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
    s=serial.Serial(COM_PORT,115200,timeout=2,write_timeout=2);time.sleep(0.5)
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
            while running and time.time()<end: time.sleep(0.3)
        except Exception as e:
            print(f"   ⚠️ Connection issue ({e}), reconnecting...");time.sleep(2)
            try: s.close()
            except: pass
            try:
                s=serial.Serial(COM_PORT,115200,timeout=2,write_timeout=2);time.sleep(0.5)
                spad(s,bytearray([0x01,0xef,0x69,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0xc5,0xd3]))
                time.sleep(0.5);s.read(23)
            except Exception as re:
                print(f"   ❌ Reconnect failed: {re}");time.sleep(2)
    try: s.close()
    except: pass
    print("\n✅ Stopped.")

if __name__=="__main__": main()
