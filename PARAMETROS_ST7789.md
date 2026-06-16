# Parámetros ST7789 para GMT020-02 - Guía de Troubleshooting

## Problema: No se ve nada en la pantalla

El GMT020-02 de 2.0" necesita la configuración correcta. Aquí están **todas las opciones** para probar:

---

## 1. **RESOLUCIÓN (width, height)**

Para display de 2.0" ST7789:

```python
# ✓ OPCIÓN 1: Horizontal (Recomendada para 2.0")
width=320,
height=240,

# ✓ OPCIÓN 2: Vertical
width=240,
height=320,
```

Si usas vertical, ajusta `rotation`:

---

## 2. **ROTACIÓN (rotation)**

```python
rotation=0    # Sin rotar (portrait si width=240)
rotation=90   # Girar 90° a la izquierda
rotation=180  # Girar 180°
rotation=270  # Girar 90° a la derecha (landscape si width=320)
```

**Recomendación**: Empieza con `rotation=0` y ajusta según lo que veas.

---

## 3. **OFFSETS (x_offset / y_offset o colstart / rowstart)**

El GMT020-02 puede necesitar correcciones de posición:

```python
# ✓ INTENTA ESTAS COMBINACIONES:

# Opción 1 (Sin offset)
x_offset=0,
y_offset=0,

# Opción 2 (Offset común para 320x240)
x_offset=0,
y_offset=20,

# Opción 3 (Offset alternativo)
x_offset=35,
y_offset=0,

# Opción 4 (Ambos offsets)
x_offset=35,
y_offset=20,
```

---

## 4. **MODO COLOR (bgr, invert)**

```python
# ✓ OPCIÓN 1 (Recomendada - colores correctos)
bgr=True,
invert=True,

# ✓ OPCIÓN 2 (Si los colores se ven extraños)
bgr=False,
invert=True,

# ✓ OPCIÓN 3 (Si todo está invertido)
bgr=True,
invert=False,

# ✓ OPCIÓN 4 (Colores completamente invertidos)
bgr=False,
invert=False,
```

---

## 5. **BAUDRATE (velocidad SPI)**

```python
# Si tienes errores de comunicación, reduce la velocidad:

baudrate=32000000,  # 32MHz (rápido, puede fallar)
baudrate=24000000,  # 24MHz (recomendado para mayores velocidades)
baudrate=16000000,  # 16MHz (estable)
baudrate=8000000,   # 8MHz (muy estable, más lento)
```

---

## 6. **MATRIZ DE COMBINACIONES PARA PROBAR**

Si nada funciona, prueba estas combinaciones ordenadas por probabilidad:

| # | width | height | rotation | y_offset | x_offset | bgr | invert | Notas |
|---|-------|--------|----------|----------|----------|-----|--------|-------|
| 1 | 320 | 240 | 0 | 0 | 0 | True | True | DEFAULT |
| 2 | 320 | 240 | 90 | 0 | 0 | True | True | Girado |
| 3 | 320 | 240 | 0 | 20 | 0 | True | True | Con offset Y |
| 4 | 320 | 240 | 0 | 0 | 35 | True | True | Con offset X |
| 5 | 240 | 320 | 270 | 0 | 0 | True | True | Vertical rotado |
| 6 | 320 | 240 | 0 | 0 | 0 | False | True | BGR invertido |
| 7 | 320 | 240 | 0 | 0 | 0 | True | False | Colores normales |
| 8 | 320 | 240 | 0 | 20 | 35 | True | True | Ambos offsets |

---

## 7. **PINES SPI CORRECTOS**

Verifica que uses estos pines en Raspberry Pi Zero 2W:

```python
# PINES SPI (son fijos en Pi Zero 2W)
clock=board.SCK      # GPIO11
MOSI=board.MOSI      # GPIO10
MISO=board.MISO      # GPIO9

# PINES CONTROL (ajustables)
cs_pin = board.CE0       # GPIO8 (Chip Select)
dc_pin = board.D25       # GPIO25 (Data/Command) - PRUEBA ESTOS:
                         # board.D25, board.D27, board.D17
rst_pin = board.D24      # GPIO24 (Reset) - PRUEBA: D4, D24, D27

# BACKLIGHT
backlight = board.D18    # GPIO18 (PWM) - PRUEBA: D18, D17, D26
```

---

## 8. **SCRIPT DE PRUEBA CON LOGGING**

Usa `hola_mundo.py` y modifica estos valores:

```python
display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=16000000,    # ← CAMBIA AQUÍ
    width=320,            # ← CAMBIA AQUÍ
    height=240,           # ← CAMBIA AQUÍ
    y_offset=0,           # ← CAMBIA AQUÍ
    x_offset=0,           # ← CAMBIA AQUÍ
    rotation=0,           # ← CAMBIA AQUÍ
    bgr=True,             # ← CAMBIA AQUÍ
    invert=True           # ← CAMBIA AQUÍ
)
```

---

## 9. **DIAGNÓSTICO: ¿QUÉ SIGNIFICA CADA SÍNTOMA?**

| Síntoma | Probable causa | Solución |
|---------|---|---|
| Pantalla en blanco/negro | Pin DC incorrecto | Prueba D25, D27, D17 |
| Texto cortado o desplazado | Offsets incorrectos | Ajusta y_offset, x_offset |
| Colores extraños | BGR o invert incorrecto | Cambia bgr/invert |
| Pantalla no enciende | Backlight no activo | Verifica pin backlight |
| Imagen borrosa/corrupta | Baudrate muy alto | Reduce a 16MHz |
| Pantalla muestra nada en absoluto | Pines SPI o CS malos | Verifica SCK, MOSI, MISO, CE0 |

---

## 10. **RECOMENDACIÓN FINAL PARA GMT020-02**

Basado en la búsqueda, el GMT020-02 típicamente funciona con:

```python
display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=16000000,
    width=320,
    height=240,
    y_offset=0,      # O prueba 20
    x_offset=0,      # O prueba 35
    rotation=0,      # O prueba 90 para landscape
    bgr=True,
    invert=True
)
```

**Si aún no funciona**, los parámetros más probables a cambiar son:
1. `dc_pin` (prueba D25, D27, D17)
2. `y_offset` (prueba 20)
3. `rotation` (prueba 90)
4. `bgr` y `invert` (prueba False)
