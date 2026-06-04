#!/bin/bash
# Script de instalación rápida para Raspberry Pi Zero 2W
# Ejecutar con: bash install.sh

set -e  # Salir si hay algún error

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Instalador - RPI Zero 2W (Pantalla OLED + Cámara)    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Verificar si se ejecuta con sudo
if [[ $EUID -ne 0 ]]; then
   echo "⚠️  Este script debe ejecutarse con sudo"
   echo "Intenta: sudo bash install.sh"
   exit 1
fi

echo "[1/6] Actualizando sistema..."
apt-get update
apt-get upgrade -y

echo "[2/6] Instalando dependencias del sistema..."
apt-get install -y python3-pip python3-dev
apt-get install -y libjpeg-dev zlib1g-dev
apt-get install -y python3-pil python3-numpy
apt-get install -y python3-rpi.gpio
apt-get install -y python3-spidev
apt-get install -y i2c-tools

echo "[3/6] Habilitando SPI..."
raspi-config nonint do_spi 0
echo "✓ SPI habilitado"

echo "[4/6] Habilitando cámara..."
raspi-config nonint do_camera 0
echo "✓ Cámara habilitada"

echo "[5/6] Instalando dependencias de Python..."
pip3 install -r requirements.txt --break-system-packages

echo "[6/6] Verificando SPI..."
echo "Dispositivos SPI detectados:"
ls /dev/spidev* || echo "⚠️  No se detectó ningún dispositivo SPI"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✓ INSTALACIÓN COMPLETADA                             ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Próximos pasos:"
echo "1. Verifica las conexiones de la pantalla OLED"
echo "2. Ejecuta las pruebas: python3 test.py"
echo "3. Ejecuta la aplicación: python3 main.py"
echo ""
echo "Documentación completa: Ver README.md"
echo ""
