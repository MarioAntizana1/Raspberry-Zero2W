"""pixel_toggle_spi.py

Example that uses the `st7789_custom.ST7789` driver to write a single pixel
and change its color using direct SPI commands.

Usage: run on the Raspberry Pi with SPI enabled and correct wiring.
"""

import time
import board
import busio
import digitalio
from st7789_custom import ST7789


if __name__ == '__main__':
    # Default pins (adjust as needed)
    cs_pin = digitalio.DigitalInOut(board.CE0)
    dc_pin = digitalio.DigitalInOut(board.D25)
    rst_pin = digitalio.DigitalInOut(board.D4)
    backlight_pin = digitalio.DigitalInOut(board.D18)

    spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)

    display = ST7789(
        spi,
        cs_pin,
        dc_pin,
        rst_pin,
        width=240,
        height=320,
        rotation=3,
        baudrate=24000000,
        x_offset=0,
        y_offset=0,
        bgr=False,
        invert=True,
        backlight=backlight_pin,
    )

    x = display.width // 2
    y = display.height // 2

    try:
        print('Clearing screen before start...')
        display.fill((0, 0, 0))

        print('Drawing pixel in red...')
        display.write_pixel(x, y, (255, 0, 0))
        time.sleep(1)

        print('Changing pixel to green...')
        display.write_pixel(x, y, (0, 255, 0))
        time.sleep(1)

        print('Changing pixel to blue...')
        display.write_pixel(x, y, (0, 0, 255))
        time.sleep(1)

        print('Clearing screen after test...')
        display.fill((0, 0, 0))
        print('Done')
    except Exception as e:
        print('Error:', e)
