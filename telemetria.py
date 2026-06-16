# -*- coding: utf-8 -*-
import time
import json
import psutil
import paho.mqtt.client as mqtt
import board
import busio
import digitalio
import sys
import ssl

# Ruta del driver
sys.path.append(r"C:\Users\wenup\Documents\Raspberry-Zero2W")
try:
    import st7789_improved
    from PIL import Image, ImageDraw, ImageFont
    has_display = True

    cs_pin  = digitalio.DigitalInOut(board.CE0)
    dc_pin  = digitalio.DigitalInOut(board.D27)
    rst_pin = digitalio.DigitalInOut(board.D22)

    spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)

    disp = st7789_improved.ST7789(
        spi,
        cs_pin,
        dc_pin,
        rst_pin,
        width=240,
        height=320,
        rotation=3,
        baudrate=24000000,
        display_name='2.0"',
        bgr=True,
        invert=True,
    )
    # ====== CREAR IMAGEN ======
    image = Image.new("RGB", (disp.width, disp.height), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    # ====== FUENTE (basica, sin fuente personalizada) ======
    try:
        # Intenta usar fuente True Type si esta disponible
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except:
        # Si no, usa la fuente por defecto
        font = ImageFont.load_default()

    # ====== MOSTRAR HOLA MUNDO ======
    print("Inicializando display...")
    try:
        # Limpiar pantalla
        draw.rectangle((0, 0, disp.width, disp.height), fill=(0, 0, 0))
        
        # Escribir texto
        text = "hola mundo"
        # Centrar el texto aproximadamente
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (disp.width - text_width) // 2
        y = (disp.height - text_height) // 2
        
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
        
        # Mostrar en la pantalla
        disp.display(image)
        print("OK: hola mundo mostrado en pantalla!")
    except Exception as e:
        print("Error mostrando texto inicial:", e)
except ImportError:
    has_display = False

# ============================================================
# BROKER 1 - ThingsBoard (MQTT simple, sin TLS)
# ============================================================
THINGSBOARD_HOST = 'mqtt.thingsboard.cloud'
ACCESS_TOKEN = 'yecuiqcakhkssbxeq0z8'

client_tb = mqtt.Client()
client_tb.username_pw_set(ACCESS_TOKEN)
client_tb.connect(THINGSBOARD_HOST, 1883, 60)
client_tb.loop_start()

# ============================================================
# BROKER 2 - EMQX Cloud (MQTT over TLS/SSL, puerto 8883)
# ============================================================
EMQX_HOST = 'v762bd76.ala.us-east-1.emqxsl.com'
EMQX_PORT = 8883
EMQX_USERNAME = 'raspi'
EMQX_PASSWORD = 'uGqjFDWbnQ5ig7i'
EMQX_CLIENT_ID = 'raspi_telemetria'

client_emqx = mqtt.Client(client_id=EMQX_CLIENT_ID)
client_emqx.username_pw_set(EMQX_USERNAME, EMQX_PASSWORD)

# TLS con los certificados CA del sistema (Raspberry Pi OS los incluye)
client_emqx.tls_set(ca_certs="/etc/ssl/certs/ca-certificates.crt")

# Callback para diagnosticar la conexion
def on_connect_emqx(client, userdata, flags, rc):
    if rc == 0:
        print("[EMQX] Conectado exitosamente!")
    elif rc == 1:
        print("[EMQX] Error: Protocol version incorrecto")
    elif rc == 2:
        print("[EMQX] Error: Client ID rechazado")
    elif rc == 3:
        print("[EMQX] Error: Servidor no disponible")
    elif rc == 4:
        print("[EMQX] Error: Usuario/password incorrectos")
    elif rc == 5:
        print("[EMQX] Error: No autorizado")
    else:
        print(f"[EMQX] Error: Codigo {rc}")

client_emqx.on_connect = on_connect_emqx

client_emqx.connect(EMQX_HOST, EMQX_PORT, 60)
client_emqx.loop_start()


def get_telemetry():
    data = {}
    cpu = psutil.cpu_percent(percpu=True)
    if len(cpu) == 1:
        data['cpu'] = cpu[0]
    else:
        data.update({f'cpu{i}': c for i, c in enumerate(cpu)})
    
    if hasattr(psutil, "sensors_temperatures"):
        for n, entries in psutil.sensors_temperatures().items():
            for i, e in enumerate(entries):
                data[e.label or f"{n}_{i}"] = e.current
                
    data['ram'] = psutil.virtual_memory().percent
    data['disk'] = psutil.disk_usage('/').percent
    return data


def publish_both(data):
    """Publica la telemetria en ambos brokers."""
    payload = json.dumps(data)
    
    # CosasBoard
    result_tb = client_tb.publish('v1/devices/me/telemetry', payload)
    print(f"[ThingsBoard] publish status: {result_tb.rc}")
    
    # EMQX
    result_emqx = client_emqx.publish('v1/devices/me/telemetry', payload)
    print(f"[EMQX] publish status: {result_emqx.rc}")


try:
    while True:
        data = get_telemetry()
        publish_both(data)
        
        if has_display:
            img = Image.new('RGB', (240, 240), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            for i, (k, v) in enumerate(data.items()):
                draw.text((5, i*15), f"{k}: {v}", fill=(255, 255, 255))
            disp.display(img)
            
        time.sleep(5)
except KeyboardInterrupt:
    client_tb.loop_stop()
    client_tb.disconnect()
    client_emqx.loop_stop()
    client_emqx.disconnect()