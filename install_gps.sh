#!/bin/bash
# ============================================================
# install_gps.sh - Instalación de dependencias para GPS + Mapas
# ============================================================
# Ejecutar en Raspberry Pi:
#   chmod +x install_gps.sh
#   sudo ./install_gps.sh
# ============================================================

set -e

echo "╔══════════════════════════════════════════╗"
echo "║     Instalación GPS + Mapas             ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 1. Verificar que SPI esté habilitado
echo "[1/5] Verificando SPI..."
if ! ls /dev/spi* &>/dev/null; then
    echo "⚠ SPI no está habilitado. Habilitando..."
    sudo raspi-config nonint do_spi 0
    echo "✓ SPI habilitado. Reinicia la Pi para aplicar cambios."
else
    echo "✓ SPI OK ($(ls /dev/spi*))"
fi

# 2. Instalar dependencias del sistema
echo ""
echo "[2/5] Instalando dependencias del sistema..."
sudo apt-get update -y
sudo apt-get install -y \
    python3-pip \
    python3-pil \
    python3-serial \
    python3-requests \
    python3-numpy \
    python3-psutil \
    fonts-dejavu-core \
    || echo "⚠ Algunos paquetes ya estaban instalados"

# 3. Instalar dependencias Python
echo ""
echo "[3/5] Instalando dependencias Python..."
pip3 install --upgrade pip
pip3 install \
    pyserial \
    Pillow \
    staticmap \
    requests \
    adafruit-blinka \
    adafruit-circuitpython-ssd1306 \
    paho-mqtt \
    psutil

# 4. Verificar pyserial
echo ""
echo "[4/5] Verificando pyserial..."
python3 -c "import serial; print(f'pyserial {serial.__version__} OK')"
python3 -c "from staticmap import StaticMap; print('staticmap OK')" || echo "⚠ staticmap no disponible (opcional)"
python3 -c "from PIL import Image; print(f'Pillow OK')"

# 5. Probar parseo de GPS
echo ""
echo "[5/5] Prueba rápida - leyendo GPS..."
echo "Ejecuta manualmente:"
echo "  sudo python3 -c \"from gps_parser import *; p=GPSParser('/dev/ttyUSB2',115200); p.set_callback(lambda d:print(d)); p.start(); import time; time.sleep(10); p.stop()\""
echo ""

echo "╔══════════════════════════════════════════╗"
echo "║     Instalación completa!               ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Para ejecutar la app:"
echo "  sudo python3 gps_display_app.py"
echo ""
echo "O probar componentes individualmente:"
echo "  sudo python3 gps_parser.py        # Solo GPS (debug)"
echo "  sudo python3 test_gmt020_dual.py  # Solo pantallas"
echo "  sudo python3 map_renderer.py      # Solo mapa (genera /tmp/test_map.png)"
