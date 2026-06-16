# Adafruit ST7735/ST7789 Library - Contenido en Experimento-pantalla

## Ubicación
`c:\Users\wenup\Documents\Raspberry-Zero2W\Experimento-pantalla\Adafruit_ST7735_and_ST7789_Library\`

## Estructura de la Librería

### Archivos Principales (C++/Arduino)

**Jerarquía de clases**:
```
Adafruit_SPITFT (base.h/base.cpp - no incluido en esta carpeta)
    ↓
Adafruit_ST77xx.h / Adafruit_ST77xx.cpp
    - Clase base para ST7735, ST7789, ST7796S
    - Comando: displayInit()
    - Comando: setAddrWindow()
    - Comando: enableDisplay()
    - Comando: enableTearing()
    - Comando: enableSleep()
    ↓
Adafruit_ST7789.h / Adafruit_ST7789.cpp
    - Especialización para ST7789
    - Tabla de inicialización generic_st7789[]
    - setRotation() (manejo de offsets)
    - init() (cálculo de offsets por modelo)
```

### Archivos de la Carpeta

```
Adafruit_ST7735_and_ST7789_Library/
├── Adafruit_ST7735.h              # Header para ST7735 (no usado)
├── Adafruit_ST7735.cpp            # Implementación ST7735 (no usado)
├── Adafruit_ST7789.h              # Header para ST7789 ✅
├── Adafruit_ST7789.cpp            # Implementación ST7789 ✅
├── Adafruit_ST77xx.h              # Header base ST77xx ✅
├── Adafruit_ST77xx.cpp            # Implementación base ST77xx ✅
├── Adafruit_ST7796S.h             # Header para ST7796S (no usado)
├── Adafruit_ST7796S.cpp           # Implementación ST7796S (no usado)
├── Adafruit_SPITFT.h              # (posible header faltante)
├── library.properties             # Metadatos npm/Arduino
├── README.txt                     # Documentación
├── CMakeLists.txt                 # Configuración build
└── examples/
    ├── graphicstest/
    │   └── graphicstest.ino        # Ejemplo gráficos general
    ├── graphicstest_st7789/
    │   └── graphicstest_st7789.ino # Ejemplo ST7789 específico ✅
    ├── graphicstest_feather_esp32s2_tft/
    │   └── graphicstest_feather_esp32s2_tft.ino
    ├── graphicstest_hallowing_m0/
    ├── graphicstest_pybadge_pygamer/
    ├── graphicstest_tft_gizmo/
    ├── ST7796S_demo/
    │   └── ST7796S_demo.ino
    ├── displayOnOffTest/
    │   └── displayOnOffTest.ino    # Test encendido/apagado
    └── shieldtest/
        └── shieldtest.ino
```

---

## Análisis de Contenido Clave

### 1. Tabla de Inicialización (Adafruit_ST7789.cpp)

```c
static const uint8_t PROGMEM generic_st7789[] = {
    9,                              // 9 comandos
    ST77XX_SWRESET,   ST_CMD_DELAY, 150,
    ST77XX_SLPOUT,    ST_CMD_DELAY, 10,
    ST77XX_COLMOD,    1+ST_CMD_DELAY, 0x55, 10,
    ST77XX_MADCTL,    1,            0x08,
    ST77XX_CASET,     4,            0x00, 0, 0, 240,
    ST77XX_RASET,     4,            0x00, 0, 320>>8, 320&0xFF,
    ST77XX_INVON,     ST_CMD_DELAY, 10,
    ST77XX_NORON,     ST_CMD_DELAY, 10,
    ST77XX_DISPON,    ST_CMD_DELAY, 10
};
```

**Nota importante**: Aquí ves que CASET tiene 4 bytes (0x00, 0, 0, 240) = X:0-240
Y RASET tiene (0x00, 0, 320>>8, 320&0xFF) = Y:0-320

Esto confirma que ST7789 tiene 320x240 RAM interno.

---

### 2. Cálculo de Offsets (Adafruit_ST7789.cpp)

```c
if (width == 240 && height == 240) {
    _rowstart = (320 - height);          // 80
    _colstart = _colstart2 = (240 - width);  // 0
} else if (width == 135 && height == 240) {
    _rowstart = (int)((320 - height) / 2);   // 40
    _colstart = (int)((240 - width + 1) / 2);
} else {
    // 240x320, 1.47", 1.69", 1.9", 2.0"
    _rowstart = (int)((320 - height) / 2);   // 0
    _colstart = (int)((240 - width) / 2);    // 0
}
```

---

### 3. Rotación Completa (Adafruit_ST7789.cpp)

Las 4 rotaciones usan diferentes bits MADCTL:

| Rotación | MADCTL | MX | MY | MV |
|----------|--------|----|----|-----|
| 0 (0°) | 0x60 | ✅ | ✅ | ❌ |
| 1 (90°) | 0xA0 | ❌ | ✅ | ✅ |
| 2 (180°) | 0x00 | ❌ | ❌ | ❌ |
| 3 (270°) | 0x60 | ✅ | ❌ | ✅ |

---

## Ejemplos de Uso (Arduino)

### graphicstest_st7789.ino (Extraído)

```cpp
#include "Adafruit_ST7789.h"
#include "Adafruit_GFX.h"

#define TFT_CS         10
#define TFT_RST         9
#define TFT_DC          8

Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);

void setup(void) {
  Serial.begin(9600);
  
  tft.init(240, 320);  // Init con ancho/alto
  
  tft.setRotation(3);  // Rotación 3
  tft.fillScreen(ST77XX_BLACK);
  
  tft.drawLine(0, 0, tft.width()-1, tft.height()-1, ST77XX_RED);
}

void loop() {
  // ...
}
```

---

## Implementación de displayInit() (Adafruit_ST77xx.cpp)

```cpp
void Adafruit_ST77xx::displayInit(const uint8_t *addr) {
  uint8_t numCommands, cmd, numArgs;
  uint16_t ms;

  numCommands = pgm_read_byte(addr++);
  while (numCommands--) {
    cmd = pgm_read_byte(addr++);
    numArgs = pgm_read_byte(addr++);
    ms = numArgs & ST_CMD_DELAY;  // Bit alto = delay presente
    numArgs &= ~ST_CMD_DELAY;
    sendCommand(cmd, addr, numArgs);
    addr += numArgs;
    
    if (ms) {
      ms = pgm_read_byte(addr++);
      if (ms == 255) ms = 500;  // 255 = 500ms
      delay(ms);
    }
  }
}
```

**Patrón**: La tabla codifica comandos, args, y tiempos de espera.

---

## Comandos ST7789 Documentados (de Adafruit_ST77xx.h)

```c
#define ST77XX_NOP         0x00
#define ST77XX_SWRESET     0x01   // Software reset
#define ST77XX_RDDID       0x04   // Read display ID
#define ST77XX_SLPIN       0x10   // Sleep in
#define ST77XX_SLPOUT      0x11   // Sleep out
#define ST77XX_INVOFF      0x20   // Inversion off
#define ST77XX_INVON       0x21   // Inversion on
#define ST77XX_DISPOFF     0x28   // Display off
#define ST77XX_DISPON      0x29   // Display on
#define ST77XX_CASET       0x2A   // Column address set
#define ST77XX_RASET       0x2B   // Row address set
#define ST77XX_RAMWR       0x2C   // RAM write
#define ST77XX_RAMRD       0x2E   // RAM read
#define ST77XX_MADCTL      0x36   // Memory access control
#define ST77XX_COLMOD      0x3A   // Color mode

#define ST77XX_MADCTL_MY   0x80   // Row address order
#define ST77XX_MADCTL_MX   0x40   // Column address order
#define ST77XX_MADCTL_MV   0x20   // Row/col exchange
#define ST77XX_MADCTL_ML   0x10   // Vertical refresh order
#define ST77XX_MADCTL_RGB  0x00   // RGB pixel order
```

---

## Lo que Incorporé en st7789_improved.py

1. **Tabla de modelos** (similar a init() de Adafruit)
2. **Cálculo automático de offsets** basado en display_name
3. **Rotación completa** con intercambio de ancho/alto (como Adafruit)
4. **set_addr_window()** (compatible API Adafruit)
5. **Métodos de control**: display_on(), display_off(), invert(), sleep()
6. **Inicialización genérica** (tabla compactada)

---

## Cómo Usar la Librería Original (Si Necesitas C++)

1. Descargar en Arduino IDE o platformio
2. Incluir headers
3. Instanciar: `Adafruit_ST7789 tft(cs, dc, rst);`
4. Inicializar: `tft.init(240, 320);`
5. Usar métodos: `tft.setRotation()`, `tft.fillScreen()`, etc.

---

## Conclusión

La librería de Adafruit es muy completa y profesional. Mi análisis mostró que:

✅ **Correctamente implementado en st7789_improved.py**:
- Auto-cálculo de offsets
- Rotación con intercambio de dimensiones
- Soporte multi-pantalla
- Control (on/off, invert, sleep)

❌ **No en st7789_custom.py** (por eso está incompleto para rotaciones 1,3)

El **próximo paso** sería migrar ejemplos a st7789_improved.py o crear adaptadores
compatibles que usen la API de Adafruit simplificada.
