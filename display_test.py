#!/usr/bin/env python3
"""
Prueba de pantalla OLED GMT020-02 sobre SPI.
Muestra texto, líneas y patrones para verificar el display.
"""

import time
from display import Display


def main():
    print("Iniciando prueba de pantalla OLED...")
    
    display = Display()
    
    try:
        display.clear()
        display.show_text("Hola Mundo", x=28, y=10)
        display.show_text("Prueba SPI", x=20, y=30)
        time.sleep(3)
        
        display.clear()
        display.show_multiline_text(
            "Display OLED\nSPI / RPI Zero 2W\nGPIO 10,11,22,27,4",
            x=10, y=10, line_spacing=15
        )
        time.sleep(4)
        
        display.clear()
        display.show_text("Mostrando", x=30, y=5)
        display.show_text("patrones...", x=20, y=20)
        time.sleep(2)
        
        for i in range(3):
            display.clear()
            display.show_text(f"Patron {i+1}", x=30, y=5)
            display.show_text("###########", x=15, y=25)
            display.show_text("***********", x=15, y=40)
            time.sleep(2)
        
        display.clear()
        display.show_text("Test completo", x=15, y=20)
        display.show_text("Presiona Ctrl+C", x=5, y=40)
        time.sleep(3)
        
    except KeyboardInterrupt:
        print("Interrumpido por el usuario")
    except Exception as e:
        print(f"Error durante la prueba de pantalla: {e}")
    finally:
        display.cleanup()
        print("Prueba finalizada")


if __name__ == '__main__':
    main()
