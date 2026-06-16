# Prueba completa para ST7789 2.0" 240x320 en Raspberry Pi
# Usa el driver personalizado st7789_custom.py y verifica colores, rotaciones y texto.

import board
import busio
import digitalio
import time
from PIL import Image, ImageDraw, ImageFont
from st7789_custom import ST7789

# Pines estándar Raspberry Pi SPI
CS_PIN = board.CE0
DC_PIN = board.D25
RST_PIN = board.D4
BL_PIN = board.D18  # Retroiluminación (ajusta si tu pantalla usa otro pin)

# Configuraciones para probar
CONFIGS = [
    {'rotation': 0, 'bgr': True, 'invert': False},
    {'rotation': 1, 'bgr': True, 'invert': False},
    {'rotation': 2, 'bgr': True, 'invert': False},
    {'rotation': 3, 'bgr': True, 'invert': False},
    {'rotation': 3, 'bgr': False, 'invert': False},
    {'rotation': 3, 'bgr': True, 'invert': True},
]

COLORS = [
    ('Rojo', (255, 0, 0)),
    ('Verde', (0, 255, 0)),
    ('Azul', (0, 0, 255)),
    ('Blanco', (255, 255, 255)),
    ('Negro', (0, 0, 0)),
]


def create_display(config):
    spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs = digitalio.DigitalInOut(CS_PIN)
    dc = digitalio.DigitalInOut(DC_PIN)
    rst = digitalio.DigitalInOut(RST_PIN)
    backlight = digitalio.DigitalInOut(BL_PIN)

    return ST7789(
        spi,
        cs,
        dc,
        rst,
        width=240,
        height=320,
        baudrate=24000000,
        rotation=config['rotation'],
        x_offset=0,
        y_offset=0,
        bgr=config['bgr'],
        invert=config['invert'],
        backlight=backlight,
    )


def show_test_text(display, text):
    image = Image.new('RGB', (display.width, display.height), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (display.width - text_width) // 2
    y = (display.height - text_height) // 2
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    display.display(image)


def fill_color(display, color, label=None):
    image = Image.new('RGB', (display.width, display.height), color=color)
    if label:
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
        except Exception:
            font = ImageFont.load_default()
        draw.text((10, 10), label, font=font, fill=(255, 255, 255) if sum(color) < 382 else (0, 0, 0))
    display.display(image)


def run_full_test():
    print('Iniciando prueba completa ST7789...')

    for idx, config in enumerate(CONFIGS, start=1):
        print(f"\nConfiguración {idx}/{len(CONFIGS)}: rotation={config['rotation']} bgr={config['bgr']} invert={config['invert']}")
        try:
            display = create_display(config)
            for name, color in COLORS:
                print(f'  Mostrando color {name}')
                fill_color(display, color, label=name)
                time.sleep(1)

            print('  Mostrando texto de prueba')
            show_test_text(display, f"rot={config['rotation']}")
            time.sleep(2)

            show_test_text(display, 'hola mundo')
            time.sleep(2)

            print('  Prueba completada para esta configuración')
        except Exception as exc:
            print(f'  ERROR en configuración: {exc}')
        finally:
            print('  Pausando antes de la próxima configuración...')
            time.sleep(1)

    print('\nPrueba completa finalizada.')


if __name__ == '__main__':
    run_full_test()
