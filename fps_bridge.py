import os
import time
import glob
import json

# Configuración del puente
LOG_DIR = os.path.expanduser("~/mangohud_logs")
TARGET_FILE_FPS = "/tmp/turing_fps"
TARGET_FILE_JSON = "/tmp/mangohud_stats.json"

def get_stats():
    log_files = glob.glob(os.path.join(LOG_DIR, "*_*.csv")) + glob.glob(os.path.join(LOG_DIR, "*_*.log"))
    if not log_files:
        return None
    
    latest_log = max(log_files, key=os.path.getmtime)
    
    # CRÍTICO: Si el archivo de log no se ha actualizado en los últimos 3 segundos, 
    # asumimos que el juego se cerró y devolvemos None.
    if (time.time() - os.path.getmtime(latest_log)) > 3:
        return None
        
    try:
        with open(latest_log, 'r') as f:
            lines = f.readlines()
            if len(lines) < 3: return None
            
            header = None
            data_line = None
            for i, line in enumerate(lines):
                if line.startswith("fps,"):
                    header = line.strip().split(",")
                    data_line = lines[-1].strip().split(",")
                    break
            
            if not header or not data_line or len(header) != len(data_line):
                return None

            stats = {}
            for i, key in enumerate(header):
                try:
                    val = float(data_line[i])
                    if key in ["fps", "gpu_core_clock", "gpu_mem_clock", "cpu_mhz"]:
                        stats[key] = int(val)
                    else:
                        stats[key] = round(val, 2)
                except:
                    stats[key] = data_line[i]
            
            return stats
    except:
        return None

if __name__ == "__main__":
    print(f"--- Puente de Estadísticas MangoHud (V2 - Inteligente) ---")
    last_state = None
    
    # Nos aseguramos de que el directorio exista
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Limpiamos archivos al empezar
    if os.path.exists(TARGET_FILE_JSON): os.remove(TARGET_FILE_JSON)
    
    try:
        while True:
            stats = get_stats()
            if not stats:
                if last_state != "no_log":
                    print(f"Esperando juego activo...")
                    if os.path.exists(TARGET_FILE_JSON): os.remove(TARGET_FILE_JSON)
                    last_state = "no_log"
            else:
                if last_state != "ok":
                    print(f"¡Juego Detectado! Enviando datos...")
                    last_state = "ok"
                
                with open(TARGET_FILE_JSON, "w") as f:
                    json.dump(stats, f)
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nPuente detenido.")
