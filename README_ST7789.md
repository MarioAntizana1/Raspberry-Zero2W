ST7789 Minimal Driver & Tests

Archivos principales:
- `st7789_custom.py` - driver ST7789 minimal SPI con comandos directos
- `hola_mundo2.py` - muestra "hola mundo" usando el driver personalizado
- `pixel_toggle_spi.py` - ejemplo que escribe un solo píxel y cambia su color
- `st7789_test_all.py` - prueba exhaustiva de colores, rotaciones y modos

Requisitos:
- Raspberry Pi con SPI habilitado (raspi-config)
- Python 3.x
- Paquetes: `Pillow` (PIL) y `adafruit-blinka` para `busio`/`digitalio`
  - Instalación ejemplo:

```bash
sudo apt update
sudo apt install -y python3-pip
pip3 install pillow adafruit-blinka
```

Uso rápido:

1) Probar píxel (SPI puro):

```bash
python3 pixel_toggle_spi.py
```

2) Mostrar "hola mundo":

```bash
python3 hola_mundo2.py
```

3) Prueba completa (colores y rotaciones):

```bash
python3 st7789_test_all.py
```

Ajustes comunes:
- Si tu pin DC es otro, modifica `dc_pin` en los scripts a `board.D27` o el que uses.
- Si no se ve nada, prueba cambiar `rotation` y `x_offset`/`y_offset` en `st7789_custom.py` o en el constructor de los scripts.

Notas sobre verificación:
- El script `pixel_toggle_spi.py` escribe directamente comandos SPI; ejecutar los scripts en la Pi es la forma más fiable de verificar funcionamiento.
- Si necesitas que el sistema pruebe automáticamente combinaciones de pines/offsets, puedo agregar ese script.
