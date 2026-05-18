# Turing 8.8" Smart Screen - Linux Video & Telemetry Dashboard

![Turing Dashboard](https://img.shields.io/badge/Turing-8.8%22%20Display-blue)
![Linux](https://img.shields.io/badge/OS-Linux-green)
![MangoHud](https://img.shields.io/badge/Integration-MangoHud-orange)

Un potente "dashboard" personalizado para la pantalla inteligente **Turing Smart Screen de 8.8"**, diseñado específicamente para aprovechar al máximo el hardware en entornos **Linux**. 

Este proyecto nace como un "fork" y una evolución extrema del excelente trabajo base de [mathoudebine/turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python), integrando funciones no documentadas de la pantalla.

## ✨ Características Principales

- 🎬 **Reproducción Nativa de Video (60 FPS):** A diferencia de otros proyectos que envían fotogramas lentos por USB, este script envía comandos seriales no documentados que le ordenan al chip de la pantalla leer y reproducir videos (`.mp4`) *directamente desde la memoria de pantalla*, logrando un rendimiento perfecto a 60 FPS sin saturar el bus USB.
- 📊 **Telemetría en Tiempo Real (Overlay):** Mientras la pantalla reproduce video por hardware, el script de Python dibuja encima textos y barras de rendimiento en tiempo real (CPU, GPU, RAM, Red).
- 🎮 **Integración con MangoHud:** Incluye un puente (`fps_bridge.py`) diseñado para capturar los logs de rendimiento de [MangoHud](https://github.com/flightlessmango/MangoHud) en Linux. Esto permite que tu pantalla Turing muestre los FPS y el uso del sistema exactos dentro de tus juegos en Steam/Lutris/Heroic.
- 🎨 **Totalmente Personalizable:** Utiliza archivos `theme.yaml` para definir qué métricas se muestran, en qué coordenadas, con qué fuentes y colores.

---

## 🚀 ¿Cómo Funciona?

El script principal (`turing_dashboard.py`) opera en dos fases mágicas:
1. **Fase 1 (Video):** Se conecta a la pantalla vía puerto Serial (`/dev/ttyACM0`) y envía la instrucción cruda para cargar una imagen inexistente (`>full_png_sucess\0`). Esto engaña al firmware de la pantalla y la fuerza a reproducir su video de fondo predeterminado desde la memoria de la pantalla.
2. **Fase 2 (Overlay):** Inmediatamente después, el script reutiliza el mismo puerto Serial para enviar únicamente actualizaciones de texto y barras (telemetría), dejando que el hardware de la pantalla se encargue de mezclar el video con los datos.

---

## 🛠️ Requisitos

- **Sistema Operativo:** Linux (probado en entornos de Gaming)
- **Hardware:** Pantalla Turing Smart Screen de 8.8" (Conectada por USB tipo C).
- **Python:** Python 3.10 o superior.
- **MangoHud:** Necesario si deseas medir los FPS de tus juegos.

---

## 📦 Instalación y Uso

### 1. Clonar e Instalar Dependencias
Clona este repositorio e instala las librerías necesarias:
```bash
git clone https://github.com/TU_USUARIO/turing-smart-screen-python.git
cd turing-smart-screen-python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar MangoHud (Para gamers)
Para que la pantalla muestre tus FPS, necesitas configurar MangoHud para que escriba automáticamente su log de rendimiento en tu disco, que es lo que lee nuestro script puente.

Edita o crea tu archivo de configuración de MangoHud (normalmente en `~/.config/MangoHud/MangoHud.conf`) y asegúrate de agregar estas líneas al final:
```ini
# Configuración necesaria para Turing Smart Screen
output_folder=~/mangohud_logs
autostart_log=1
log_interval=100
```
- `output_folder`: Le dice a MangoHud dónde guardar los CSV.
- `autostart_log=1`: Hace que empiece a grabar automáticamente en cuanto abres un juego.
- `log_interval=100`: Graba datos cada 100ms (10 veces por segundo) para que la pantalla se actualice súper rápido.

Una vez configurado, inicia el puente antes o mientras juegas:
```bash
python3 fps_bridge.py
```

### 3. Iniciar el Dashboard
Arranca el controlador principal de la pantalla:
```bash
python3 turing_dashboard.py
```
*(Si usas Linux, es probable que necesites permisos sobre `/dev/ttyACM0`. Puedes agregarte al grupo `dialout` o usar `sudo`).*

---

## 🤝 Créditos

- Núcleo original del proyecto y parseo de hardware por [mathoudebine](https://github.com/mathoudebine/turing-smart-screen-python).
- Adaptación para 8.8", hack de hardware SD y puente MangoHud desarrollados y afinados para Linux Gaming.


