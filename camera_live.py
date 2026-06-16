#!/usr/bin/env python3
"""camera_live.py

Vista en tiempo real de la cámara en la pantalla GMT020-02 (ST7789).
Optimizado para máximo rendimiento en Raspberry Pi Zero 2W.

Pipeline:
  Picamera2 (320×240 RGB) → numpy RGB565 → SPI → ST7789

Pines:
  CS  = CE0   (GPIO8)
  DC  = D27   (GPIO27)
  RST = D4    (GPIO4)

Uso:
  sudo python3 camera_live.py
  sudo python3 camera_live.py --fps 30
  sudo python3 camera_live.py --rotation 1
  sudo python3 camera_live.py --hflip --vflip
"""

import time
import sys
import argparse
import struct
import numpy as np

import board
import busio
import digitalio
from picamera2 import Picamera2

from st7789_improved import ST7789


DISPLAY_W = 240       # Dimensión nativa del display (portrait)
DISPLAY_H = 320       # Dimensión nativa del display (portrait)
LANDSCAPE_W = 320     # Cuando rotation=1 o 3
LANDSCAPE_H = 240


def rgb888_to_rgb565(arr: np.ndarray) -> bytes:
    """Convierte array numpy RGB888 (H,W,3) a buffer RGB565 big-endian.

    Usa operaciones vectorizadas para máximo rendimiento.
    """
    # Asegurar tipo uint16 para evitar overflow en shifts
    r = arr[:, :, 0].astype(np.uint16)
    g = arr[:, :, 1].astype(np.uint16)
    b = arr[:, :, 2].astype(np.uint16)

    rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return rgb565.astype('>u2').tobytes()


def display_raw_rgb565(display: ST7789, buf: bytes):
    """Envía un buffer RGB565 directamente al display sin conversión.

    Más rápido que display.display() porque evita la conversión PIL.
    """
    display.set_addr_window(0, 0, display.width, display.height)
    display._data(buf)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Vista en vivo de la cámara en pantalla ST7789'
    )
    parser.add_argument(
        '--fps', type=int, default=30,
        help='FPS objetivo de la cámara (default: 30). '
             'El FPS real depende del ancho de banda SPI.'
    )
    parser.add_argument(
        '--rotation', type=int, default=3, choices=[0, 1, 2, 3],
        help='Rotación del display 0-3 (default: 3 = landscape). '
             '0=portrait, 1=landscape-derecha, 2=portrait-invertido, '
             '3=landscape-izquierda'
    )
    parser.add_argument(
        '--baudrate', type=int, default=16000000,
        help='Velocidad SPI en Hz (default: 16 MHz). '
             'Frecuencias mayores son más rápidas pero propensas a ruido y pérdida de señal.'
    )
    parser.add_argument(
        '--hflip', action='store_true',
        help='Voltear imagen horizontalmente (espejo)'
    )
    parser.add_argument(
        '--vflip', action='store_true',
        help='Voltear imagen verticalmente'
    )
    parser.add_argument(
        '--show-fps', action='store_true', default=True,
        help='Mostrar FPS en consola (default: activado)'
    )
    parser.add_argument(
        '--no-show-fps', action='store_false', dest='show_fps',
        help='No mostrar FPS en consola'
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("╔══════════════════════════════════════════╗")
    print("║  Cámara en Vivo — ST7789 + Pi Zero 2W   ║")
    print("╚══════════════════════════════════════════╝")
    print()

    # ── Determinar dimensiones según rotación ──
    if args.rotation in (1, 3):
        disp_w, disp_h = LANDSCAPE_W, LANDSCAPE_H
    else:
        disp_w, disp_h = DISPLAY_W, DISPLAY_H

    # ── Inicializar display ──
    print("[1/3] Inicializando display ST7789...")
    print(f"      Rotación: {args.rotation}  →  {disp_w}×{disp_h}")
    print(f"      SPI baudrate: {args.baudrate / 1e6:.1f} MHz")

    cs_pin  = digitalio.DigitalInOut(board.CE0)
    dc_pin  = digitalio.DigitalInOut(board.D27)
    rst_pin = digitalio.DigitalInOut(board.D4)

    spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)

    display = ST7789(
        spi,
        cs_pin,
        dc_pin,
        rst_pin,
        width=DISPLAY_W,
        height=DISPLAY_H,
        rotation=args.rotation,
        baudrate=args.baudrate,
        display_name='2.0"',
        bgr=True,
        invert=True,
    )
    print(f"      → Display listo: {display.width}×{display.height}")

    # ── Inicializar cámara ──
    print("[2/3] Inicializando cámara (Picamera2)...")
    print(f"      Resolución: {disp_w}×{disp_h}")
    print(f"      FPS objetivo: {args.fps}")

    picam2 = Picamera2()

    # Configurar cámara con resolución exacta del display
    # Usar formato RGB888 para conversión directa a RGB565
    cam_config = picam2.create_video_configuration(
        main={
            "size": (disp_w, disp_h),
            "format": "RGB888",
        }
    )

    # Configurar flips si se solicitan (atributos estándar de Picamera2)
    if args.hflip:
        picam2.horizontal_flip = True
    if args.vflip:
        picam2.vertical_flip = True

    picam2.configure(cam_config)
    picam2.start()

    # Configurar FPS objetivo mediante control de duración de frame (µs)
    frame_time = int(1_000_000 / args.fps)
    try:
        picam2.set_controls({"FrameDurationLimits": (frame_time, frame_time)})
    except Exception as e:
        print(f"      [Aviso] No se pudo fijar FrameDurationLimits: {e}")

    # Esperar estabilización del auto-exposure
    print("      Esperando estabilización de cámara (1s)...")
    time.sleep(1)
    print("      → Cámara lista")
    print()

    # ── Pantalla de inicio ──
    display.fill((0, 0, 0))

    # ── Loop principal ──
    print("[3/3] Iniciando vista en vivo...")
    print("      Ctrl+C para salir")
    print()

    frame_count = 0
    fps_actual = 0.0
    t_start = time.monotonic()
    t_fps_report = t_start

    # Pre-calcular tamaño del buffer esperado
    expected_buf_size = disp_w * disp_h * 2  # RGB565 = 2 bytes/pixel

    try:
        while True:
            # Capturar frame como numpy array (H, W, 3) uint8 RGB
            frame = picam2.capture_array("main")

            # Conversión RGB888 → RGB565 (vectorizada con numpy)
            buf = rgb888_to_rgb565(frame)

            # Enviar directamente al display (bypass PIL)
            display_raw_rgb565(display, buf)

            frame_count += 1

            # Reportar FPS cada segundo
            if args.show_fps:
                t_now = time.monotonic()
                elapsed = t_now - t_fps_report
                if elapsed >= 1.0:
                    fps_actual = frame_count / elapsed
                    frame_count = 0
                    t_fps_report = t_now
                    total_time = t_now - t_start

                    # Calcular throughput SPI
                    throughput_mbps = (fps_actual * expected_buf_size * 8) / 1e6

                    sys.stdout.write(
                        f"\r  FPS: {fps_actual:5.1f}  |  "
                        f"Tiempo: {total_time:6.0f}s  |  "
                        f"SPI: {throughput_mbps:5.1f} Mbps  "
                    )
                    sys.stdout.flush()

    except KeyboardInterrupt:
        t_total = time.monotonic() - t_start
        print(f"\n\n→ Detenido después de {t_total:.1f} segundos")
        print(f"  FPS promedio: {fps_actual:.1f}")

    finally:
        print("→ Limpiando recursos...")
        try:
            picam2.stop()
            picam2.close()
            print("  ✓ Cámara cerrada")
        except Exception:
            pass
        try:
            display.fill((0, 0, 0))
            display.display_off()
            print("  ✓ Pantalla apagada")
        except Exception:
            pass
        print("→ Listo")


if __name__ == "__main__":
    main()
