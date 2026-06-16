#!/usr/bin/env python3
"""
gps_display_app.py - Aplicación principal GPS + Mapas + 2 Pantallas

Muestra:
  Pantalla #1 (CS=GPIO17): Mapa con posición actual
  Pantalla #2 (CS=GPIO23): Datos de navegación (satélites, altitud, velocidad, etc.)

Hardware:
  - SIM7600-G en /dev/ttyUSB2 (115200 baud)
  - 2x Pantallas GMT020-02 (ST7789, 240x320) en SPI compartido
  - RPi Zero 2W

Uso:
  sudo python3 gps_display_app.py

Dependencias:
  pip install pyserial Pillow staticmap requests
"""

import time
import sys
import threading
import math
import json
import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont

# Nuestros módulos
from st7789_improved import ST7789
from gps_parser import GPSParser, GPSData
from map_renderer import MapRenderer

# MQTT + Sistema
import paho.mqtt.client as mqtt
import psutil

# ═══════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ═══════════════════════════════════════════════════════

# Puertos
GPS_PORT = "/dev/ttyUSB2"
GPS_BAUD = 115200

# ── ThingsBoard ──
THINGSBOARD_HOST = 'mqtt.thingsboard.cloud'
ACCESS_TOKEN = 'yecuiqcakhkssbxeq0z8'
MQTT_PUBLISH_INTERVAL = 10  # segundos entre publicaciones MQTT

# Zoom inicial del mapa (15=calle, 16=detalle, 17=más detalle)
MAP_ZOOM = 16

# Intervalo de refresco (segundos)
REFRESH_INTERVAL = 2.0

# Historial de ruta (puntos para dibujar)
MAX_ROUTE_POINTS = 50  # Guardar últimos N puntos

# ═══════════════════════════════════════════════════════
#  PINES DE LAS PANTALLAS
# ═══════════════════════════════════════════════════════

# Pantalla #1 - MAPA
CS1_PIN = board.D17   # GPIO17
DC1_PIN = board.D27   # GPIO27
RST1_PIN = board.D22  # GPIO22

# Pantalla #2 - DATOS
CS2_PIN = board.D23   # GPIO23
DC2_PIN = board.D25   # GPIO25
RST2_PIN = board.D24  # GPIO24


class GPSDisplayApp:
    """Aplicación principal que coordina GPS + Mapas + 2 Pantallas"""

    def __init__(self):
        print("╔══════════════════════════════════════════╗")
        print("║     GPS + MAPAS + 2 PANTALLAS           ║")
        print("╚══════════════════════════════════════════╝")
        print()

        # Inicializar pantallas
        self._init_displays()

        # Inicializar renderizador de mapas
        self.map_renderer = MapRenderer(
            width=240, height=320, zoom=MAP_ZOOM
        )

        # Inicializar GPS
        self.gps = GPSParser(GPS_PORT, GPS_BAUD)
        self.gps.set_callback(self._on_gps_update)

        # Datos de ruta
        self.route_points = []
        self.last_data = GPSData()
        self.last_update_time = 0
        self.display_lock = threading.Lock()
        self.running = False

        # Estadísticas
        self.frame_count = 0
        self.start_time = time.time()

        # ── ThingsBoard MQTT ──
        self._init_mqtt()
        self.last_mqtt_publish = 0

    def _init_displays(self):
        """Inicializa ambas pantallas en el bus SPI compartido"""
        print("[INIT] Inicializando bus SPI...")
        spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)
        print(f"       SPI0: SCK=GPIO11, MOSI=GPIO10")

        # Pantalla #1 - Mapa
        print("[INIT] Pantalla #1 (MAPA) - CS=GPIO17, DC=GPIO27, RST=GPIO22")
        self.display_map = ST7789(
            spi,
            digitalio.DigitalInOut(CS1_PIN),
            digitalio.DigitalInOut(DC1_PIN),
            digitalio.DigitalInOut(RST1_PIN),
            width=240,
            height=320,
            rotation=0,          # Vertical (retrato)
            baudrate=24000000,
            display_name='2.0"',
            bgr=False,
            invert=True,
        )

        # Pantalla #2 - Datos
        print("[INIT] Pantalla #2 (DATOS) - CS=GPIO23, DC=GPIO25, RST=GPIO24")
        self.display_data = ST7789(
            spi,
            digitalio.DigitalInOut(CS2_PIN),
            digitalio.DigitalInOut(DC2_PIN),
            digitalio.DigitalInOut(RST2_PIN),
            width=240,
            height=320,
            rotation=0,          # Vertical (retrato)
            baudrate=24000000,
            display_name='2.0"',
            bgr=False,
            invert=True,
        )

        print("[INIT] Pantallas listas!")
        print()

        # Mostrar splash
        self._show_splash()

    def _show_splash(self):
        """Muestra pantalla de inicio"""
        for disp, text, color in [
            (self.display_map, "GPS MAPA", (0, 200, 255)),
            (self.display_data, "GPS DATOS", (0, 255, 128)),
        ]:
            img = Image.new("RGB", (disp.width, disp.height), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24
                )
                font_small = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14
                )
            except:
                font = ImageFont.load_default()
                font_small = font

            # Título
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            x = (disp.width - tw) // 2
            y = disp.height // 2 - 30
            draw.text((x, y), text, font=font, fill=color)

            # Subtítulo
            sub = "Iniciando..."
            bbox2 = draw.textbbox((0, 0), sub, font=font_small)
            sw = bbox2[2] - bbox2[0]
            sx = (disp.width - sw) // 2
            draw.text((sx, y + 35), sub, font=font_small, fill=(200, 200, 200))

            disp.display(img)

    # ────────────────────────────────────────────────
    #  MQTT - ThingsBoard
    # ────────────────────────────────────────────────

    def _init_mqtt(self):
        """Inicializa conexión MQTT con ThingsBoard"""
        print("[MQTT] Conectando a ThingsBoard...")
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.username_pw_set(ACCESS_TOKEN)
            self.mqtt_client.connect(THINGSBOARD_HOST, 1883, 60)
            self.mqtt_client.loop_start()
            print(f"[MQTT] Conectado a {THINGSBOARD_HOST} como {ACCESS_TOKEN[:8]}...")
        except Exception as e:
            print(f"[MQTT] Error conectando: {e}")
            self.mqtt_client = None

    def _publish_to_thingsboard(self, gps_data: GPSData):
        """Publica datos de GPS + sistema a ThingsBoard"""
        if not self.mqtt_client:
            return

        lat, lon = gps_data.get_coordinates_decimal()

        payload = {
            # GPS
            "latitude": lat,
            "longitude": lon,
            "altitude": gps_data.altitude,
            "speed": gps_data.speed_kmh,
            "speed_knots": gps_data.speed_knots,
            "track_angle": gps_data.track_angle,
            "num_satellites": gps_data.num_satellites,
            "satellites_in_view": gps_data.satellites_in_view,
            "hdop": gps_data.hdop,
            "pdop": gps_data.pdop,
            "vdop": gps_data.vdop,
            "fix_quality": gps_data.fix_quality,
            "fix_type": gps_data.fix_type,
            "has_fix": 1 if gps_data.has_fix() else 0,
            "timestamp_utc": gps_data.timestamp,
            # Sistema RPi
            **self._get_system_telemetry(),
        }

        try:
            result = self.mqtt_client.publish(
                "v1/devices/me/telemetry",
                json.dumps(payload)
            )
            if result.rc == 0:
                print(f"[MQTT] Publicado OK - Lat:{lat:.4f} Lon:{lon:.4f} "
                      f"Sats:{gps_data.num_satellites} Alt:{gps_data.altitude:.1f}m "
                      f"Vel:{gps_data.speed_kmh:.1f}km/h")
            else:
                print(f"[MQTT] Error publicación: rc={result.rc}")
        except Exception as e:
            print(f"[MQTT] Error: {e}")

    @staticmethod
    def _get_system_telemetry() -> dict:
        """Recolecta telemetría del sistema RPi"""
        data = {}

        # CPU
        cpu_percent = psutil.cpu_percent(percpu=False)
        data["cpu"] = cpu_percent
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            data["cpu_freq"] = round(cpu_freq.current, 1)

        # Temperatura CPU
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if "cpu_thermal" in temps:
                data["cpu_temp"] = round(temps["cpu_thermal"][0].current, 1)
            elif "coretemp" in temps:
                data["cpu_temp"] = round(temps["coretemp"][0].current, 1)

        # Memoria RAM
        mem = psutil.virtual_memory()
        data["ram"] = round(mem.percent, 1)
        data["ram_used_mb"] = round(mem.used / 1024 / 1024, 0)
        data["ram_total_mb"] = round(mem.total / 1024 / 1024, 0)

        # Disco
        disk = psutil.disk_usage('/')
        data["disk"] = round(disk.percent, 1)
        data["disk_used_gb"] = round(disk.used / 1024 / 1024 / 1024, 1)
        data["disk_total_gb"] = round(disk.total / 1024 / 1024 / 1024, 1)

        # Tiempo actividad
        data["uptime"] = round(time.time() - psutil.boot_time(), 0)

        return data

    # ────────────────────────────────────────────────

    def _on_gps_update(self, data: GPSData):
        """Callback cuando llegan datos nuevos del GPS"""
        self.last_data = data

    def _render_map_screen(self, data: GPSData) -> Image.Image:
        """Renderiza Pantalla #1: Mapa con posición"""
        lat, lon = data.get_coordinates_decimal()

        if data.has_fix() and lat != 0 and lon != 0:
            # Renderizar mapa
            img = self.map_renderer.render_map(lat, lon, self.route_points)
            draw = ImageDraw.Draw(img)

            # Info adicional en la parte inferior
            try:
                font_small = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11
                )
            except:
                font_small = ImageFont.load_default()

            # Barra de estado inferior
            draw.rectangle([0, 305, 239, 319], fill=(0, 0, 0))
            status = (f"Fix:{'3D' if data.fix_type == 3 else '2D' if data.fix_type == 2 else 'No'}"
                      f" | Sats:{data.num_satellites}"
                      f" | HDOP:{data.hdop:.1f}"
                      f" | Z:{MAP_ZOOM}")
            draw.text((4, 308), status, font=font_small, fill=(0, 255, 128))

        else:
            # Sin fix - pantalla de búsqueda
            img = Image.new("RGB", (240, 320), (10, 10, 20))
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18
                )
                font_small = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12
                )
            except:
                font = ImageFont.load_default()
                font_small = font

            # Animación de búsqueda
            cx, cy = 120, 140
            for i in range(4):
                angle = (time.time() * 2 + i * 1.57) % 6.28
                x = cx + int(30 * math.cos(angle))
                y = cy + int(30 * math.sin(angle))
                draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(0, 100, 255))

            # Texto
            text = "BUSCANDO GPS..."
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            draw.text(((240 - tw) // 2, 200), text, font=font, fill=(255, 200, 0))

            # Satélites visibles
            if data.satellites_in_view > 0:
                sub = f"Satelites visibles: {data.satellites_in_view}"
                bbox2 = draw.textbbox((0, 0), sub, font=font_small)
                sw = bbox2[2] - bbox2[0]
                draw.text(((240 - sw) // 2, 230), sub, font=font_small, fill=(200, 200, 200))

        return img

    def _render_data_screen(self, data: GPSData) -> Image.Image:
        """Renderiza Pantalla #2: Datos de navegación"""
        img = Image.new("RGB", (240, 320), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16
            )
            font_normal = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13
            )
            font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11
            )
        except:
            font_large = ImageFont.load_default()
            font_normal = font_large
            font_small = font_large

        lat, lon = data.get_coordinates_decimal()
        has_fix = data.has_fix()

        # Color de cabecera según estado
        header_color = (0, 200, 0) if has_fix else (255, 100, 0)
        status_text = "FIX 3D" if data.fix_type == 3 else "FIX 2D" if data.fix_type == 2 else "SIN FIX"

        # ── Cabecera ──
        draw.rectangle([0, 0, 239, 24], fill=(20, 20, 30))
        draw.text((8, 4), "GPS NAVIGATION", font=font_large, fill=(0, 200, 255))
        draw.text((170, 4), status_text, font=font_small, fill=header_color)

        # ── Línea separadora ──
        draw.line([(0, 26), (239, 26)], fill=(50, 50, 50), width=1)

        y = 32
        line_height = 21

        # ── Posición ──
        draw.text((8, y), "LAT:", font=font_normal, fill=(150, 150, 150))
        draw.text((60, y), f"{lat:.6f}° {data.lat_direction}",
                  font=font_normal, fill=(255, 255, 255))
        y += line_height

        draw.text((8, y), "LON:", font=font_normal, fill=(150, 150, 150))
        draw.text((60, y), f"{lon:.6f}° {data.lon_direction}",
                  font=font_normal, fill=(255, 255, 255))
        y += line_height

        # ── Línea ──
        y += 2
        draw.line([(8, y), (232, y)], fill=(40, 40, 40), width=1)
        y += 6

        # ── Altitud y Velocidad ──
        draw.text((8, y), "ALTITUD:", font=font_normal, fill=(150, 150, 150))
        draw.text((100, y), f"{data.altitude:.1f} {data.altitude_unit}",
                  font=font_normal, fill=(0, 255, 128))
        y += line_height

        draw.text((8, y), "VELOCIDAD:", font=font_normal, fill=(150, 150, 150))
        vel_color = (255, 255, 255) if data.speed_kmh > 0 else (150, 150, 150)
        draw.text((100, y), f"{data.speed_kmh:.1f} km/h",
                  font=font_normal, fill=vel_color)
        y += line_height

        draw.text((8, y), "RUMBO:", font=font_normal, fill=(150, 150, 150))
        draw.text((100, y), f"{data.track_angle:.1f}°",
                  font=font_normal, fill=(255, 255, 200))
        y += line_height

        # ── Línea ──
        y += 2
        draw.line([(8, y), (232, y)], fill=(40, 40, 40), width=1)
        y += 6

        # ── Satélites ──
        draw.text((8, y), "SATELITES:", font=font_normal, fill=(150, 150, 150))
        sats_color = (0, 255, 0) if data.num_satellites >= 4 else (255, 200, 0)
        draw.text((100, y), f"{data.num_satellites} / {data.satellites_in_view}",
                  font=font_normal, fill=sats_color)
        y += line_height

        # Dibujar barras de SNR de satélites
        if data.satellites:
            y += 4
            bar_y = y
            bar_height = 20
            for i, sat in enumerate(data.satellites[:8]):  # Max 8 en pantalla
                x = 8 + i * 28
                snr = sat.get('snr', 0)
                elev = sat.get('elevation', 0)

                # Color según SNR
                if snr > 30:
                    color = (0, 255, 0)
                elif snr > 20:
                    color = (255, 200, 0)
                elif snr > 10:
                    color = (255, 100, 0)
                else:
                    color = (100, 100, 100)

                # Barra
                bar_h = max(2, int(bar_height * (snr / 50)))
                draw.rectangle([x, bar_y + bar_height - bar_h,
                                x + 10, bar_y + bar_height],
                               fill=color)

                # PRN
                draw.text((x - 2, bar_y + bar_height + 2),
                          str(sat.get('prn', '?')),
                          font=font_small, fill=(200, 200, 200))

            y += bar_height + 16

        # ── Línea ──
        draw.line([(8, y), (232, y)], fill=(40, 40, 40), width=1)
        y += 6

        # ── Precisión ──
        draw.text((8, y), "HDOP:", font=font_normal, fill=(150, 150, 150))
        draw.text((80, y), f"{data.hdop:.2f}",
                  font=font_normal, fill=(255, 255, 255))
        y += line_height

        draw.text((8, y), "PDOP:", font=font_normal, fill=(150, 150, 150))
        draw.text((80, y), f"{data.pdop:.2f}",
                  font=font_normal, fill=(255, 255, 255))
        y += line_height

        draw.text((8, y), "VDOP:", font=font_normal, fill=(150, 150, 150))
        draw.text((80, y), f"{data.vdop:.2f}",
                  font=font_normal, fill=(255, 255, 255))
        y += line_height

        # ── Hora UTC ──
        if data.timestamp:
            y += 4
            draw.line([(8, y), (232, y)], fill=(40, 40, 40), width=1)
            y += 6
            # Formatear HH:MM:SS
            ts = data.timestamp
            if len(ts) >= 6:
                h, m, s = ts[:2], ts[2:4], ts[4:6]
                time_str = f"{h}:{m}:{s} UTC"
            else:
                time_str = ts
            draw.text((8, y), "HORA:", font=font_normal, fill=(150, 150, 150))
            draw.text((80, y), time_str, font=font_normal, fill=(0, 200, 255))

        # ── Pie de página ──
        draw.rectangle([0, 305, 239, 319], fill=(20, 20, 30))
        fps = self.frame_count / max(1, time.time() - self.start_time)
        draw.text((8, 308), f"FPS: {fps:.1f} | Pts: {len(self.route_points)}",
                  font=font_small, fill=(100, 100, 100))

        return img

    def start(self):
        """Inicia la aplicación"""
        self.running = True
        self.start_time = time.time()

        # Iniciar GPS
        self.gps.start()

        print("[APP] GPS iniciado. Esperando datos...")
        print("[APP] Pantalla #1 (GPIO17): Mapa")
        print("[APP] Pantalla #2 (GPIO23): Datos navegacion")
        print()

        try:
            while self.running:
                loop_start = time.time()

                # Obtener datos actuales
                data = self.gps.get_data()
                lat, lon = data.get_coordinates_decimal()

                # Actualizar ruta si hay fix y posición válida
                if data.has_fix() and lat != 0 and lon != 0:
                    # Evitar duplicados muy cercanos
                    if not self.route_points or self._distance(
                        self.route_points[-1][0], self.route_points[-1][1],
                        lat, lon
                    ) > 0.0001:  # ~10m
                        self.route_points.append((lat, lon))
                        if len(self.route_points) > MAX_ROUTE_POINTS:
                            self.route_points = self.route_points[-MAX_ROUTE_POINTS:]

                # Renderizar pantallas
                with self.display_lock:
                    img_map = self._render_map_screen(data)
                    img_data = self._render_data_screen(data)

                    # Actualizar pantallas
                    self.display_map.display(img_map)
                    self.display_data.display(img_data)

                self.frame_count += 1

                # ── Publicar a ThingsBoard (cada MQTT_PUBLISH_INTERVAL seg) ──
                now = time.time()
                if now - self.last_mqtt_publish >= MQTT_PUBLISH_INTERVAL:
                    self._publish_to_thingsboard(data)
                    self.last_mqtt_publish = now

                # Control de tasa de refresco
                elapsed = time.time() - loop_start
                sleep_time = REFRESH_INTERVAL - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n[APP] Deteniendo...")
        finally:
            self.cleanup()

    @staticmethod
    def _distance(lat1, lon1, lat2, lon2):
        """Distancia aprox en grados (no precisa pero rápida)"""
        return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5

    def cleanup(self):
        """Limpia recursos"""
        print("[APP] Limpiando...")
        self.gps.stop()

        # Desconectar MQTT
        if hasattr(self, 'mqtt_client') and self.mqtt_client:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                print("[MQTT] Desconectado de ThingsBoard")
            except:
                pass

        # Apagar pantallas
        try:
            for disp, name in [(self.display_map, "Mapa"),
                               (self.display_data, "Datos")]:
                disp.fill((0, 0, 0))
                disp.display_off()
                print(f"[APP] Pantalla {name} apagada")
        except:
            pass

        print("[APP] Aplicacion terminada.")


# ═══════════════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    app = GPSDisplayApp()
    app.start()
