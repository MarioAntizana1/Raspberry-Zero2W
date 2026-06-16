# Análisis Comparativo: Adafruit_ST7789 vs st7789_custom.py

## Resumen General

La librería de **Adafruit** (C++/Arduino) y nuestro **st7789_custom.py** tienen enfoques diferentes:
- **Adafruit**: Arquitectura jerárquica, flexible, soporte para múltiples pantallas
- **st7789_custom.py**: Simple, directo, específico para GMT020-02 (240x320)

---

## 1. Arquitectura

### Adafruit (C++)
```
Adafruit_SPITFT (base SPI/GPIO)
    ↓
Adafruit_ST77xx (ST7735/ST7789/ST7796S común)
    ↓
Adafruit_ST7789 (especialización ST7789)
```
**Ventaja**: Código reutilizable, soporte para múltiples pantallas ST77xx.

### st7789_custom.py
```
ST7789 (clase única)
    - SPI directo
    - GPIO directo
    - Inicialización específica
```
**Ventaja**: Más fácil de entender y debuggear.

---

## 2. Inicialización

### Adafruit
- **Tabla PROGMEM** con comandos secuenciales
- Funciones genéricas para leer y ejecutar
- Soporta tiempos de espera variables por comando
- Tabla genérica para ST7789 (9 comandos)

```c
static const uint8_t PROGMEM generic_st7789[] = {
    9,                              // 9 comandos
    ST77XX_SWRESET,   ST_CMD_DELAY, 150,  // Reset + 150ms
    ST77XX_SLPOUT,    ST_CMD_DELAY, 10,   // Sleep out + 10ms
    ST77XX_COLMOD,    1+ST_CMD_DELAY, 0x55, 10,  // 16-bit color + delay
    ...
};
```

### st7789_custom.py
- **Inicialización inline** en `_initialize_display()`
- Tiempos fijos de espera por comando
- Específica para GMT020-02

```python
def _initialize_display(self):
    self._command(_SWRESET)
    time.sleep(0.15)
    self._command(_SLPOUT)
    time.sleep(0.12)
    ...
```

**Diferencia**: Adafruit es más flexible; st7789_custom es más directo.

---

## 3. Rotación (setRotation)

### Adafruit - Manejo complejo
```c
case 0:
    madctl = MX | MY | RGB;
    _xstart = _colstart;
    _ystart = _rowstart;
    _width = windowWidth;
    _height = windowHeight;
    break;
case 1:
    madctl = MY | MV | RGB;
    _xstart = _rowstart;
    _ystart = _colstart2;
    _height = windowWidth;
    _width = windowHeight;
    break;
```

**Características**:
- Ajusta MADCTL (registro de control de memoria)
- Ajusta offsets X/Y internos (`_xstart`, `_ystart`)
- **Intercambia ancho/alto** en rotaciones 1 y 3
- Maneja `_colstart2` (offset desde la derecha) para pantallas asimétricas

### st7789_custom.py - Manejo simple
```python
def set_rotation(self, rotation: int):
    if rotation == 0:
        madctl = _MX | _MY | _RGB
    elif rotation == 1:
        madctl = _MY | _MV | _RGB
    elif rotation == 2:
        madctl = _RGB
    else:
        madctl = _MX | _MV | _RGB
```

**Diferencia**: 
- ✅ st7789_custom es más simple y legible
- ❌ No ajusta ancho/alto dinámicamente en rotación
- ❌ No usa offsets internos correctamente

---

## 4. Manejo de Offsets (muy importante para pantallas asimétricas)

### Adafruit
```c
if (width == 240 && height == 240) {
    _rowstart = (320 - height);      // 80
    _rowstart2 = 0;
    _colstart = _colstart2 = (240 - width);  // 0
} else if (width == 135 && height == 240) {
    _rowstart = _rowstart2 = (int)((320 - height) / 2);  // 40
    _colstart = (int)((240 - width + 1) / 2);
    _colstart2 = (int)((240 - width) / 2);
} else {
    // 240x320, 1.47", 1.69", 1.9", 2.0"
    _rowstart = _rowstart2 = (int)((320 - height) / 2);  // 0
    _colstart = _colstart2 = (int)((240 - width) / 2);   // 0
}
```

**Propósito**: Diferentes pantallas ST7789 tienen diferentes resoluciones físicas internas (320x240) pero diferentes tamaños de pantalla útiles (240x320, 135x240, etc.).

### st7789_custom.py
```python
self.x_offset = x_offset  # Simple, no cálculo automático
self.y_offset = y_offset
```

**Diferencia**: Adafruit calcula automáticamente los offsets según el tamaño; st7789_custom requiere pasarlos manualmente.

---

## 5. Escritura en Memoria RAM (setAddrWindow)

### Adafruit (optimizado)
```c
void Adafruit_ST77xx::setAddrWindow(uint16_t x, uint16_t y, uint16_t w, uint16_t h) {
    x += _xstart;
    y += _ystart;
    uint32_t xa = ((uint32_t)x << 16) | (x + w - 1);  // CASET: x_start | x_end
    uint32_t ya = ((uint32_t)y << 16) | (y + h - 1);  // RASET: y_start | y_end
    
    writeCommand(ST77XX_CASET);
    SPI_WRITE32(xa);  // 4 bytes en una sola transferencia
    
    writeCommand(ST77XX_RASET);
    SPI_WRITE32(ya);
    
    writeCommand(ST77XX_RAMWR);
}
```

**Ventaja**: Usa SPI_WRITE32 (optimizador con 32 bits), muy rápido.

### st7789_custom.py
```python
def _set_window(self, x0: int, y0: int, x1: int, y1: int):
    x0 += self.x_offset
    x1 += self.x_offset
    y0 += self.y_offset
    y1 += self.y_offset
    
    self._command(_CASET, bytes([0x00, x0 & 0xFF, 0x00, x1 & 0xFF]))
    self._command(_RASET, bytes([0x00, y0 & 0xFF, 0x00, y1 & 0xFF]))
    self._command(_RAMWR)
```

**Diferencia**: Ambos funcionan, pero Adafruit es más compacto con 32 bits.

---

## 6. Escritura de Píxeles

### Adafruit
No tiene `write_pixel()` explícito. Usa `fillRect()` o buffers internos de GFX.

### st7789_custom.py
```python
def write_pixel(self, x: int, y: int, color=(255, 255, 255)):
    if not (0 <= x < self.width and 0 <= y < self.height):
        raise ValueError('Pixel out of bounds')
    self._set_window(x, y, x, y)
    pixel = _color565(*color)
    self._data(bytes([(pixel >> 8) & 0xFF, pixel & 0xFF]))
```

**Ventaja**: st7789_custom tiene esto explícitamente para debugging.

---

## 7. Tabla Comparativa de Comandos ST7789

| Comando | Código | Adafruit | st7789_custom | Descripción |
|---------|--------|----------|----------------|-------------|
| SWRESET | 0x01 | ✅ | ✅ | Software reset |
| SLPOUT | 0x11 | ✅ | ✅ | Sleep out |
| COLMOD | 0x3A | ✅ | ✅ | Color mode (0x55 = 16-bit RGB565) |
| MADCTL | 0x36 | ✅ | ✅ | Memory access control (rotación) |
| CASET | 0x2A | ✅ | ✅ | Column address set |
| RASET | 0x2B | ✅ | ✅ | Row address set |
| RAMWR | 0x2C | ✅ | ✅ | RAM write |
| INVON | 0x21 | ✅ | ✅ | Inversion on |
| INVOFF | 0x20 | ✅ | ✗ | Inversion off (no implementado en st7789) |
| NORON | 0x13 | ✅ | ✅ | Normal on |
| DISPON | 0x29 | ✅ | ✅ | Display on |
| DISPOFF | 0x28 | ✅ | ✗ | Display off |
| SLPIN | 0x10 | ✅ | ✗ | Sleep in |

---

## 8. Problemas y Observaciones

### En st7789_custom.py
1. ❌ No calcula offsets automáticamente por tamaño
2. ❌ Rotación no ajusta ancho/alto dinámicamente
3. ❌ No tiene `invert_off()` o `display_off()`
4. ❌ Falta soporte para diferentes tamaños de pantalla (135x240, 240x240)
5. ⚠️ El `_set_window()` toma (x0, y0, x1, y1) pero Adafruit usa (x, y, w, h)
6. ⚠️ Sin método para limpiar pantalla ("fill") usando SPI directo

### En Adafruit_ST7789
1. ❌ Diseño complejo (jerarquía de 3 clases)
2. ❌ Requiere Adafruit_GFX y Adafruit_SPITFT
3. ⚠️ No tiene `write_pixel()` simple

---

## Recomendación: st7789_improved.py

Propongo crear una versión mejorada que combine:
- **Simplicidad de st7789_custom.py**
- **Flexibilidad de Adafruit** (offsets automáticos, soporte multi-pantalla)
- **Manejo robusto de rotación**
- **Métodos adicionales**: `invert()`, `sleep()`, `display_on()`, `display_off()`
- **API clara** basada en Adafruit pero simplificada

**Características principales**:
```python
class ST7789:
    def __init__(self, spi, cs, dc, rst, 
                 width=240, height=320,
                 display_name="2.0\"",  # Detecta offsets automáticamente
                 rotation=0, bgr=False, invert=True, backlight=None):
        # Auto-calcula offsets según width, height, display_name
        # Inicializa con tabla de comandos
        
    def set_rotation(self, r):
        # Ajusta MADCTL, ancho, alto, offsets internos
        
    def setAddrWindow(self, x, y, w, h):
        # Compatible con Adafruit API
        
    def display_on(self):
    def display_off(self):
    def invert(self, enable):
    def sleep(self, enable):
    
    def write_pixel(self, x, y, color):
    def fill_rect(self, x, y, w, h, color):
    def fill(self, color):
```

---

## Conclusión

| Aspecto | Adafruit | st7789_custom |
|--------|----------|---------------|
| Simplicidad | ❌ Compleja | ✅ Simple |
| Flexibilidad | ✅ Muy flexible | ❌ Rígida |
| Documentación | ✅ Excelente | ⚠️ Básica |
| Performance | ✅ Optimizada | ⚠️ Aceptable |
| Mantenibilidad | ❌ Difícil | ✅ Fácil |
| Multi-pantalla | ✅ Soporta 10+ | ❌ Solo GMT020-02 |

**Solución óptima**: Crear una versión **intermedia** que sea simple pero flexible.
