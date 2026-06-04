# GUÍA DE SOLUCIÓN DE PROBLEMAS
# Raspberry Pi Zero 2W - Pantalla OLED + Cámara

## 🔴 Problemas Comunes y Soluciones

### 1. LA PANTALLA NO APARECE

#### Síntoma: 
"No se detecta la pantalla OLED" o "Error de SPI"

#### Soluciones:

**Paso 1: Verificar conexiones físicas**
```bash
# En la Raspberry Pi, ejecuta:
ls /dev/spidev*
```
Si no ves `/dev/spidev0.0` o `/dev/spidev0.1`, la pantalla no está conectada correctamente.

**Paso 2: Verificar SPI está habilitado**
```bash
sudo raspi-config
# Ve a: Interface Options → SPI → Yes
sudo reboot
```

**Paso 3: Verificar el bus SPI**
```bash
ls /dev/spidev*
```
Si no ves `/dev/spidev0.0` o `/dev/spidev0.1`, SPI no está habilitado correctamente.

**Paso 4: Verificar cables y voltaje**
- Verifica que MOSI y SCLK estén en los pines correctos (GPIO10 y GPIO11)
- Asegúrate de que GND esté conectado
- Verifica que haya 5V o 3.3V según lo que requiera tu pantalla

---

### 2. LA CÁMARA NO FUNCIONA

#### Síntoma:
"Cámara no detectada" o "Error al capturar foto"

#### Soluciones:

**Paso 1: Verificar que la cámara esté habilitada**
```bash
sudo raspi-config
# Ve a: Interface Options → Camera → Si → OK
sudo reboot
```

**Paso 2: Verificar que la cámara esté conectada**
```bash
vcgencmd get_camera
# Debería mostrar: supported=1 detected=1
```

Si muestra `detected=0`, la cámara no está conectada correctamente:
- Apaga la Raspberry Pi
- Verifica que el cable CSI esté firmemente insertado
- Enciende nuevamente

**Paso 3: Verificar permisos**
```bash
# Ejecuta la aplicación con sudo
sudo python3 main.py
```

**Paso 4: Liberar la cámara si está en uso**
```bash
# Verifica si picamera está en uso
lsof | grep picamera
# Si aparece algo, termina ese proceso:
sudo killall -9 python3
```

---

### 3. ERROR: "ModuleNotFoundError: No module named 'board'"

#### Síntoma:
No se encuentran las librerías de Adafruit

#### Soluciones:

```bash
# Reinstalar todas las dependencias
sudo pip3 install -r requirements.txt

# O instalar cada una por separado:
sudo pip3 install RPi.GPIO
sudo pip3 install adafruit-circuitpython-ssd1306
sudo pip3 install adafruit-blinka
sudo pip3 install board
sudo pip3 install busio
sudo pip3 install Pillow
```

---

### 4. ERROR: "RuntimeError: No module named board"

#### Síntoma:
El módulo board no se encuentra aunque esté instalado

#### Soluciones:

**Opción 1: Instalar librerías de sistema necesarias**
```bash
sudo apt-get install -y python3-dev
sudo apt-get install -y libffi-dev
sudo apt-get install -y libssl-dev
```

**Opción 2: Reinstalar con pip3 como usuario**
```bash
pip3 install --user board busio
```

---

### 5. PANTALLA Y CÁMARA FUNCIONAN PERO MUY LENTO

#### Síntoma:
Los FPS son muy bajos o hay lag

#### Soluciones:

**Paso 1: Reducir resolución de cámara**
Edita `config.py`:
```python
CAMERA_CONFIG = {
    'resolution': (1280, 720),  # Reducido de 1920x1088
    'framerate': 30,
}
```

**Paso 2: Verificar temperatura**
```bash
vcgencmd measure_temp
```
Si la temperatura es > 80°C, la Raspberry Pi se está limitando. Mejora la ventilación.

**Paso 3: Usar pantalla de menor actualización**
```python
# En examples.py o main.py, aumenta el delay:
time.sleep(0.1)  # En lugar de 0.033
```

---

### 6. ERROR: "SPI: Permission denied"

#### Síntoma:
Error de permisos al acceder a SPI

#### Soluciones:

```bash
# Opción 1: Ejecutar con sudo
sudo python3 main.py

# Opción 2: Agregar usuario al grupo gpio (permite acceso a SPI)
sudo usermod -a -G gpio pi
# Requiere reinicio:
sudo reboot
```

---

### 7. ERROR: "GPIO: RuntimeError"

#### Síntoma:
Error al acceder a los pines GPIO

#### Soluciones:

```bash
# Opción 1: Ejecutar con sudo
sudo python3 main.py

# Opción 2: Limpiar GPIO de procesos anteriores
sudo gpio reset  # Si está disponible

# Opción 3: Reiniciar
sudo reboot
```

---

### 8. PANTALLA MUESTRA SOLO PIXELS BLANCOS O NEGROS

#### Síntoma:
La pantalla no muestra el contenido correctamente

#### Soluciones:

**Paso 1: Verificar pines GPIO**
Comprueba que los pines en `config.py` sean correctos:
```python
DISPLAY_CONFIG = {
    'rst_pin': 4,      # GPIO4 para RST
    'dc_pin': 27,      # GPIO27 para DC
    'cs_pin': 22,      # GPIO22 para CS
}
```

**Paso 2: Reiniciar la pantalla**
```python
# En Python:
from display import Display
display = Display()
display.clear()
display.cleanup()
```

**Paso 3: Verificar contraste**
Algunos displays OLED tienen ajustes de contraste. Consulta el datasheet de tu GMT020-02.

---

### 9. CÁMARA CAPTURA PERO IMAGEN ESTÁ OSCURA O BORROSA

#### Síntoma:
Las fotos capturadas no se ven bien

#### Soluciones:

```bash
# Verificar configuración de la cámara
sudo vcgencmd set_config display_hdmi_rotate 0

# Cambiar orientación en config.py:
CAMERA_CONFIG = {
    'rotation': 90,  # O 180, 270
}
```

---

### 10. APLICACIÓN SE CONGELA

#### Síntoma:
main.py se queda congelado

#### Soluciones:

**Paso 1: Presiona Ctrl+C** para salir
```bash
# Si no responde, en otra terminal:
sudo pkill -9 python3
```

**Paso 2: Ejecutar test.py primero**
```bash
python3 test.py
```

**Paso 3: Verificar permisos**
```bash
# Ejecutar con sudo
sudo python3 main.py
```

---

## ✅ PRUEBAS DE DIAGNÓSTICO

### Test completo del sistema
```bash
python3 test.py
```

### Test individual - Pantalla
```bash
python3 -c "from display import Display; d=Display(); d.show_text('Test'); import time; time.sleep(3); d.cleanup()"
```

### Test individual - Cámara
```bash
python3 -c "from camera import Camera; c=Camera(); c.capture_photo('/home/pi/test.jpg'); c.cleanup()"
```

### Verificar librerías
```bash
python3 -c "import board; print('board OK')"
python3 -c "import RPi.GPIO; print('GPIO OK')"
python3 -c "from picamera2 import Picamera2; print('Camera OK')"
```

---

## 🔧 COMANDOS ÚTILES

### Ver logs del sistema
```bash
sudo journalctl -u application-name -f
```

### Verificar espacio en disco
```bash
df -h
```

### Verificar memoria disponible
```bash
free -h
```

### Monitorear temperatura en tiempo real
```bash
watch -n1 'vcgencmd measure_temp'
```

### Ver procesos Python en ejecución
```bash
ps aux | grep python
```

---

## 📞 OBTENER AYUDA

Si los pasos anteriores no funcionan:

1. Ejecuta:
   ```bash
   python3 main.py 2>&1 | tee debug.log
   ```

2. Comparte el contenido de `debug.log`

3. Incluye:
   - Modelo de Raspberry Pi
   - Versión de Raspberry Pi OS
   - Salida de `vcgencmd get_config int | grep -E "gpu_mem|camera"`

---

## 📝 NOTAS IMPORTANTES

- Siempre apaga la Raspberry Pi antes de hacer cambios de hardware
- Asegúrate de usar una fuente de alimentación estable (5V, ≥2A)
- La Raspberry Pi Zero 2W es más lenta que modelos posteriores
- El SPI puede ser sensible a ruido; usa cables cortos y de buena calidad
- Los pines GPIO son delicados; evita cortocircuitos

---

**Última actualización**: Junio 2026
