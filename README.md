# Aplicación Raspberry Pi Zero 2W - Pantalla OLED + Cámara

Aplicación Python para Raspberry Pi Zero 2W que integra una pantalla OLED GMT020-02 Ver1.1 y la cámara integrada del dispositivo.

## Características

✅ **Pantalla OLED GMT020-02 Ver1.1**
- Display SPI SSD1306 (128x64 píxeles)
- Mostrar texto en la pantalla
- Soporte para múltiples líneas
- Mostrar imágenes
- Reset en GPIO04
- Data/Command en GPIO27  
- Chip Select en GPIO22  
- SPI0 con MOSI GPIO10 y SCLK GPIO11

✅ **Cámara Raspberry Pi**
- Captura de fotos
- Grabación de video
- Obtención de frames en tiempo real
- Estadísticas de FPS

✅ **Interfaz Amigable**
- Menú interactivo en la pantalla
- Mensajes de estado
- Manejo de errores robusto

## Requisitos de Hardware

- **Raspberry Pi Zero 2W**
- **Pantalla OLED GMT020-02 Ver1.1**
- **Cámara Raspberry Pi (CSI)**
- **Cable SPI (para la pantalla)**
- **Fuente de alimentación estable (5V, 2A mínimo)**

## Conexiones

### Pantalla OLED (GMT020-02)

| Pantalla | Pin GPIO |
|----------|----------|
| GND      | GND      |
| VCC      | 5V o 3.3V|
| MOSI     | GPIO10 (SPI MOSI) |
| SCLK     | GPIO11 (SPI SCLK) |
| RST      | GPIO4            |
| DC       | GPIO27           |
| CS       | GPIO22           |

### Cámara

| Cámara    | Conexión |
|-----------|----------|
| Ribbon   | CSI Port |

## Instalación

### 1. Preparar el Sistema

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Habilitar SPI y Cámara

```bash
sudo raspi-config
```

- Ir a **Interface Options** → **SPI** → **Yes**
- Ir a **Interface Options** → **Camera** → **Yes**
- Reiniciar el dispositivo

```bash
sudo reboot
```

### 3. Instalar Dependencias del Sistema

```bash
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y libjpeg-dev zlib1g-dev
sudo apt-get install -y python3-pil python3-numpy
sudo apt-get install -y python3-rpi.gpio python3-spidev
```

### 4. Clonar/Descargar el Proyecto

```bash
cd ~
git clone <url-del-repositorio>
cd Raspberry-Zero2W
```

### 5. Crear Entorno Virtual (Opcional pero Recomendado)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 6. Instalar Dependencias de Python

```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar la Aplicación Principal

```bash
python3 main.py
```

Abre en tu navegador:

```bash
http://<ip-de-tu-raspberry>:5000
```

### Probar solo la pantalla

```bash
python3 display_test.py
```

La aplicación hará lo siguiente:

1. **Inicializar la pantalla OLED**
2. **Mostrar "Hola Mundo"** en la pantalla

### Probar solo la pantalla

```bash
python3 display_test.py
```

Este script muestra texto y patrones básicos para verificar que la pantalla OLED está funcionando correctamente en SPI.
3. **Inicializar la cámara**
4. **Capturar una foto de prueba**
5. **Mostrar estadísticas en tiempo real** (FPS, frames contados)

Para salir, presiona **Ctrl+C**

## Descripción de Archivos

### `config.py`
Archivo de configuración centralizado:
- Pines GPIO de la pantalla (RST, DC, CS)
- Pines SPI de la pantalla
- Resolución de la cámara
- Modo de depuración

### `display.py`
Módulo para controlar la pantalla OLED:
- `Display()` - Clase principal
- `show_text()` - Mostrar texto simple
- `show_multiline_text()` - Mostrar múltiples líneas
- `show_image()` - Mostrar imagen
- `clear()` - Limpiar pantalla

### `camera.py`
Módulo para controlar la cámara:
- `Camera()` - Clase principal
- `capture_photo()` - Capturar foto
- `start_recording()` / `stop_recording()` - Grabar video
- `get_frame()` - Obtener frame en tiempo real

### `main.py`
Aplicación principal que integra pantalla y cámara.

## Solución de Problemas

### La pantalla no aparece

1. Verifica las conexiones SPI
2. Comprueba que SPI esté habilitado:
   ```bash
   ls /dev/spidev*
   ```
3. Verifica que los pines estén configurados en `config.py`:
   - `rst_pin`: 4
   - `dc_pin`: 27
   - `cs_pin`: 22

### La cámara no funciona

1. Verifica que la cámara esté conectada al puerto CSI
2. Habilita la cámara en `raspi-config`
3. Comprueba el estado:
   ```bash
   vcgencmd get_camera
   ```

### Errores de GPIO

1. Asegúrate de ejecutar con permisos de administrador si es necesario:
   ```bash
   sudo python3 main.py
   ```
2. Verifica que los pines no estén en uso por otros procesos

## Personalización

### Cambiar Resolución de Cámara

Edita `config.py`:
```python
CAMERA_CONFIG = {
    'resolution': (1280, 720),  # Cambiar resolución
    'framerate': 30,
    'rotation': 0,
}
```

### Cambiar Pines GPIO

Edita `config.py`:
```python
DISPLAY_CONFIG = {
    'rst_pin': 4,      # Cambiar GPIO del RST
    'dc_pin': 27,      # Cambiar GPIO del DC
    'cs_pin': 22,      # Cambiar GPIO del CS
    ...
}
```

### Cambiar Texto Inicial

Edita `main.py` y modifica las llamadas a `display.show_text()`.

## Ejemplos Adicionales

### Capturar Foto Personalizada

```python
from camera import Camera

camera = Camera()
camera.capture_photo('/home/pi/mi_foto.jpg')
camera.cleanup()
```

### Grabar Video

```python
from camera import Camera
import time

camera = Camera()
camera.start_recording('/home/pi/video.h264')
time.sleep(10)  # Grabar durante 10 segundos
camera.stop_recording()
camera.cleanup()
```

### Mostrar Imagen en Pantalla

```python
from display import Display

display = Display()
display.show_image('/home/pi/imagen.png')
time.sleep(5)
display.cleanup()
```

## Notas Importantes

- **Temperatura**: La RPI Zero 2W se calienta bajo carga. Asegúrate de tener ventilación adecuada.
- **Alimentación**: Usa una fuente estable de 5V con al menos 2A.
- **SPI**: Asegúrate de que SPI esté habilitado y el bus `spidev` esté presente.
- **Permisos**: En algunos casos necesitarás privilegios de root para acceder a GPIO y SPI.

## Licencia

Este proyecto es de código abierto. Úsalo libremente.

## Autor

Creado para Raspberry Pi Zero 2W

---

¿Necesitas ayuda? Revisa los logs de depuración habilitando `DEBUG = True` en `config.py`.
