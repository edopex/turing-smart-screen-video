# Turing 8.8" Smart Screen - Linux Video & Telemetry Dashboard

Un potente dashboard personalizado y suite de control visual para la pantalla inteligente Turing Smart Screen de 8.8", diseñado específicamente para aprovechar al máximo el hardware en entornos Linux.

Este proyecto es una evolucion extrema del trabajo base de mathoudebine/turing-smart-screen-python, integrando funciones no documentadas de la pantalla, optimizaciones de velocidad vectorizadas y una suite de configuracion visual e interactiva.

---

## Caracteristicas Principales

### Reproduccion Nativa de Video (60 FPS)
A diferencia de otros proyectos que envian fotogramas lentos por USB, este script envia comandos seriales no documentados que le ordenan al chip de la pantalla leer y reproducir videos (.mp4) directamente desde la memoria interna de la pantalla (tarjeta SD), logrando un rendimiento perfecto a 60 FPS sin saturar el bus USB.

### Telemetria en Tiempo Real Optimizada
Mientras la pantalla reproduce video por hardware, el script de Python dibuja encima textos y barras de rendimiento en tiempo real (CPU, GPU, RAM, Red). El procesamiento de imagen ha sido acelerado mediante calculo matricial vectorizado con NumPy, reduciendo el tiempo de actualizacion de 1.9 segundos a apenas 0.3 segundos por cuadro.

### Centro de Control Grafico (Turing Control Center)
Una suite visual e intuitiva construida en Tkinter que permite administrar los servicios en segundo plano con un solo clic. Muestra el estado actual del dashboard y del puente MangoHud (RUNNING / STOPPED) de manera limpia, permitiendo iniciar o apagar los servicios de forma silenciosa sin abrir consolas ni terminales de sistema.

### Editor de Diseno Interactiva (Drag & Drop)
Integrado dentro del Centro de Control, este editor visual muestra un lienzo a escala 50% de la pantalla fisica. Permite arrastrar libremente con el mouse cualquier texto o etiqueta en tiempo real y ver como se desplaza en vivo de forma instantanea en tu pantalla fisica de 8.8". Las coordenadas se guardan automaticamente en un archivo JSON local.

### Integracion con MangoHud
Incluye un puente (fps_bridge.py) disenado para capturar los logs de rendimiento de MangoHud en Linux. Esto permite que tu pantalla Turing muestre los FPS y el tiempo de cuadro exactos dentro de tus juegos en Steam, Lutris o Heroic.

### Inicio Automatico
Configurado para iniciar ambos servicios en segundo plano de manera 100% silenciosa al iniciar sesion en el sistema operativo, garantizando que tu pantalla empiece a funcionar de inmediato al encender la PC.

---

## Estructura del Proyecto

- turing_dashboard.py: Controlador de renderizado principal que procesa la telemetria y dibuja sobre el overlay de la pantalla.
- turing_control_center.py: Interfaz grafica principal (Tkinter) para arrancar, detener y abrir la configuracion de los servicios en segundo plano.
- layout_editor.py: Lienzo interactivo para posicionar los elementos graficos con arrastrar y soltar.
- fps_bridge.py: Puente para leer y formatear las metricas de rendimiento de MangoHud en disco.
- layout.json: Registro de coordenadas X e Y para cada uno de los elementos de texto en la pantalla.

---

## Requisitos

- Sistema Operativo: Linux (probado en entornos de Gaming)
- Hardware: Pantalla Turing Smart Screen de 8.8" (Conectada por USB y con tarjeta SD interna).
- Python: Python 3.10 o superior, con dependencias (Pillow, NumPy, PySerial, Psutil).
- MangoHud: Opcional, necesario si deseas medir los FPS de tus juegos en tiempo real.

---

## Instalacion y Configuracion

### 1. Clonar e Instalar Dependencias
Clona este repositorio e instala las librerias necesarias:
```bash
git clone https://github.com/TU_USUARIO/turing-smart-screen-python.git
cd turing-smart-screen-python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar Acceso al Puerto Serial
Asegurate de que tu usuario tenga permisos de lectura y escritura en el puerto serial de la pantalla (por defecto /dev/ttyACM1):
```bash
sudo usermod -aG dialout $USER
```
*(Es necesario cerrar sesion y volver a entrar para que se apliquen los cambios de grupo).*

### 3. Configurar MangoHud
Para que la pantalla muestre tus FPS dentro de los juegos, edita o crea tu archivo de configuracion de MangoHud (normalmente en ~/.config/MangoHud/MangoHud.conf) y agrega estas lineas al final:
```ini
output_folder=~/mangohud_logs
autostart_log=1
log_interval=100
```
- output_folder: Define la ruta donde MangoHud guardara sus reportes temporales CSV.
- autostart_log=1: Inicia el reporte de forma automatica al arrancar cualquier juego.
- log_interval=100: Registra datos cada 100ms para mantener el dashboard actualizado.

---

## Uso

### Lanzamiento Diario
Simplemente busca "Turing Control Center" en el menu de aplicaciones de tu escritorio Linux o ejecuta:
```bash
python3 turing_control_center.py
```
Desde este panel grafico podras iniciar, detener y abrir el editor de diseno a mano alzada.

### Personalizacion del Diseno
Haz clic en el boton "Edit Layout" dentro de la tarjeta del Dashboard en el Centro de Control para abrir el lienzo. Arrastra las etiquetas de prueba y colocalas a tu gusto. Al cerrar la ventana, las posiciones se guardaran de manera automatica en layout.json.

---

## Creditos

- Nucleo original del proyecto y parseo de hardware por mathoudebine.
- Adaptacion para pantalla de 8.8", ingenieria inversa del bus de video SD, optimizacion matricial NumPy, suite grafica y puente MangoHud desarrollados para Linux Gaming.
