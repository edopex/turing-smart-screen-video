# SPDX-License-Identifier: GPL-3.0-or-later
import math
import json
import os
import time
from abc import ABC, abstractmethod
from typing import List

import library.sensors.sensors_python as sys_sensors

class CustomDataSource(ABC):
    @abstractmethod
    def as_numeric(self) -> float:
        pass
    @abstractmethod
    def as_string(self) -> str:
        pass
    @abstractmethod
    def last_values(self) -> List[float]:
        pass

class MangoHudBase(CustomDataSource):
    JSON_PATH = "/tmp/mangohud_stats.json"
    STALE_THRESHOLD = 5
    
    _cached_data = {}
    _last_mtime = 0
    _history = {}
    _is_in_game = False

    @classmethod
    def _update_context(cls):
        if not os.path.exists(cls.JSON_PATH):
            cls._is_in_game = False
            return
        
        try:
            mtime = os.path.getmtime(cls.JSON_PATH)
            if (time.time() - mtime) > cls.STALE_THRESHOLD:
                cls._is_in_game = False
            else:
                cls._is_in_game = True
                if mtime > cls._last_mtime:
                    with open(cls.JSON_PATH, 'r') as f:
                        cls._cached_data = json.load(f)
                    cls._last_mtime = mtime
        except:
            cls._is_in_game = False

    def __init__(self, key, unit="", format_str=""):
        self.key = key
        self.unit = unit
        self.format_str = format_str
        if self.key not in MangoHudBase._history:
            MangoHudBase._history[self.key] = [math.nan] * 10
        self.value = math.nan

    def last_values(self) -> List[float]:
        return MangoHudBase._history.get(self.key, [math.nan] * 10)

class MangoHudMode(MangoHudBase):
    def __init__(self):
        super().__init__("mode")
    def as_numeric(self) -> float:
        self._update_context()
        return 1.0 if self._is_in_game else 0.0
    def as_string(self) -> str:
        self._update_context()
        return "GAMING" if self._is_in_game else "DESKTOP"

class MangoHudFPS(MangoHudBase):
    def __init__(self):
        super().__init__("fps", " FPS", "%d")
    def as_numeric(self) -> float:
        self._update_context()
        self.value = self._cached_data.get("fps", 180) if self._is_in_game else 180
        MangoHudBase._history["fps"].append(self.value)
        MangoHudBase._history["fps"].pop(0)
        return self.value
    def as_string(self) -> str:
        return str(int(self.as_numeric()))

class MangoHudCpuLoad(MangoHudBase):
    def __init__(self):
        super().__init__("cpu_load", "%", "%.1f")
    def as_numeric(self) -> float:
        self._update_context()
        self.value = self._cached_data.get("cpu_load", sys_sensors.Cpu.percentage(interval=0.1)) if self._is_in_game else sys_sensors.Cpu.percentage(interval=0.1)
        MangoHudBase._history["cpu_load"].append(self.value)
        MangoHudBase._history["cpu_load"].pop(0)
        return self.value
    def as_string(self) -> str:
        return f"{self.as_numeric():.1f}%"

class MangoHudGpuLoad(MangoHudBase):
    def __init__(self):
        super().__init__("gpu_load", "%", "%.1f")
    def as_numeric(self) -> float:
        self._update_context()
        if self._is_in_game:
            self.value = self._cached_data.get("gpu_load", 0)
        else:
            stats = sys_sensors.Gpu.stats()
            self.value = stats[0] if not math.isnan(stats[0]) else 0
        MangoHudBase._history["gpu_load"].append(self.value)
        MangoHudBase._history["gpu_load"].pop(0)
        return self.value
    def as_string(self) -> str:
        return f"{self.as_numeric():.1f}%"

class MangoHudCpuTemp(MangoHudBase):
    def __init__(self):
        super().__init__("cpu_temp", "°C", "%d")
    def as_numeric(self) -> float:
        self._update_context()
        self.value = self._cached_data.get("cpu_temp", sys_sensors.Cpu.temperature()) if self._is_in_game else sys_sensors.Cpu.temperature()
        if math.isnan(self.value): self.value = 0
        MangoHudBase._history["cpu_temp"].append(self.value)
        MangoHudBase._history["cpu_temp"].pop(0)
        return self.value
    def as_string(self) -> str:
        return f"{int(self.as_numeric())}°C"

class MangoHudGpuTemp(MangoHudBase):
    def __init__(self):
        super().__init__("gpu_temp", "°C", "%d")
    def as_numeric(self) -> float:
        self._update_context()
        if self._is_in_game:
            self.value = self._cached_data.get("gpu_temp", 0)
        else:
            stats = sys_sensors.Gpu.stats()
            self.value = stats[4] if not math.isnan(stats[4]) else 0
        MangoHudBase._history["gpu_temp"].append(self.value)
        MangoHudBase._history["gpu_temp"].pop(0)
        return self.value
    def as_string(self) -> str:
        return f"{int(self.as_numeric())}°C"

class MangoHudRam(MangoHudBase):
    def __init__(self):
        super().__init__("ram_used", " GB", "%.2f")
    def as_numeric(self) -> float:
        self._update_context()
        self.value = self._cached_data.get("ram_used", sys_sensors.Memory.virtual_used()/(1024**3)) if self._is_in_game else sys_sensors.Memory.virtual_used()/(1024**3)
        return self.value
    def as_string(self) -> str:
        return f"{self.as_numeric():.2f} GB"

class MangoHudVram(MangoHudBase):
    def __init__(self):
        super().__init__("gpu_vram_used", " GB", "%.2f")
    def as_numeric(self) -> float:
        self._update_context()
        if self._is_in_game:
            self.value = self._cached_data.get("gpu_vram_used", 0)
        else:
            stats = sys_sensors.Gpu.stats()
            self.value = stats[2]/1024 if not math.isnan(stats[2]) else 0
        return self.value
    def as_string(self) -> str:
        return f"{self.as_numeric():.2f} GB"

class MangoHudCpuPower(MangoHudBase):
    def __init__(self):
        super().__init__("cpu_power", " W", "%d")
    def as_numeric(self) -> float:
        self._update_context()
        val = self._cached_data.get("cpu_power", 0)
        if val > 0:
            self.value = val
        else:
            # FÓRMULA INTELIGENTE: Si no hay lectura real, fluctuar según la carga
            # Base 15W + (Carga * 0.6) para simular actividad real
            load = sys_sensors.Cpu.percentage(interval=0)
            if math.isnan(load): load = 0
            self.value = 15 + (load * 0.6)
        return self.value
    def as_string(self) -> str:
        return f"{int(self.as_numeric())} W"

class MangoHudGpuPower(MangoHudBase):
    def __init__(self):
        super().__init__("gpu_power", " W", "%d")
    def as_numeric(self) -> float:
        self._update_context()
        val = self._cached_data.get("gpu_power", 0)
        if val > 0:
            self.value = val
        else:
            # LECTURA REAL DEL SISTEMA (AMD HWmon2)
            try:
                with open("/sys/class/hwmon/hwmon2/power1_average", "r") as f:
                    # El valor está en microvatios, pasamos a W
                    self.value = int(f.read().strip()) / 1000000
            except:
                self.value = 10 # Fallback
        return self.value
    def as_string(self) -> str:
        return f"{int(self.as_numeric())} W"

class MangoHudFrametime(MangoHudBase):
    def __init__(self):
        super().__init__("frametime", " ms", "%.1f")
    def as_numeric(self) -> float:
        self._update_context()
        return self._cached_data.get("frametime", 0) if self._is_in_game else 0
    def as_string(self) -> str:
        return f"{self.as_numeric():.1f} ms"

class MangoHudGpuVoltage(MangoHudBase):
    def __init__(self):
        super().__init__("gpu_voltage", " V", "%.3f")
    def as_numeric(self) -> float:
        self._update_context()
        val = self._cached_data.get("gpu_voltage", 0)
        if val > 0:
            self.value = val
        else:
            try:
                with open("/sys/class/hwmon/hwmon2/in0_input", "r") as f:
                    self.value = int(f.read().strip()) / 1000 # mV a V
            except:
                self.value = 0.8
        return self.value
    def as_string(self) -> str:
        return f"{self.as_numeric():.3f} V"
