#!/usr/bin/env python3
"""
Ejemplos Prácticos - Usos comunes de la aplicación
Descomenta el ejemplo que quieras ejecutar
"""

import time
from display import Display
from camera import Camera

# ============================================================================
# EJEMPLO 1: Mostrar "Hola Mundo" simple
# ============================================================================
def ejemplo_hola_mundo():
    """Ejemplo simple - Mostrar 'Hola Mundo' en pantalla"""
    print("Ejecutando: Hola Mundo")
    
    display = Display()
    display.clear()
    display.show_text("Hola Mundo", x=30, y=25)
    
    time.sleep(3)
    display.cleanup()


# ============================================================================
# EJEMPLO 2: Mostrar información del sistema
# ============================================================================
def ejemplo_info_sistema():
    """Muestra información del sistema en la pantalla"""
    import os
    import subprocess
    
    print("Ejecutando: Información del Sistema")
    
    display = Display()
    
    # Obtener temperatura
    try:
        temp = subprocess.check_output(['vcgencmd', 'measure_temp']).decode()
        temp = temp.replace('temp=', '').replace("'C\n", '')
    except:
        temp = "N/A"
    
    # Obtener uptime
    try:
        uptime = subprocess.check_output(['uptime', '-p']).decode().strip()
    except:
        uptime = "N/A"
    
    display.clear()
    display.show_multiline_text(
        f"Sistema RPI\n"
        f"Temp: {temp}C\n"
        f"Uptime: {uptime}",
        x=5, y=10, line_spacing=15
    )
    
    time.sleep(5)
    display.cleanup()


# ============================================================================
# EJEMPLO 3: Capturar foto y mostrar en pantalla
# ============================================================================
def ejemplo_capturar_foto():
    """Captura una foto y muestra confirmación"""
    print("Ejecutando: Capturar Foto")
    
    display = Display()
    camera = Camera()
    
    display.clear()
    display.show_text("Capturando...", x=25, y=25)
    
    timestamp = int(time.time())
    photo_file = f"/home/pi/foto_{timestamp}.jpg"
    
    if camera.capture_photo(photo_file):
        display.clear()
        display.show_text("Foto guardada!", x=20, y=20)
        display.show_text(photo_file[:18], x=5, y=40)
        print(f"Foto guardada: {photo_file}")
    else:
        display.clear()
        display.show_text("Error!", x=40, y=25)
        print("Error al capturar foto")
    
    time.sleep(3)
    display.cleanup()
    camera.cleanup()


# ============================================================================
# EJEMPLO 4: Mostrar contador
# ============================================================================
def ejemplo_contador():
    """Muestra un contador en la pantalla"""
    print("Ejecutando: Contador (10 segundos)")
    
    display = Display()
    
    for i in range(10, 0, -1):
        display.clear()
        display.show_text(f"Contador: {i}", x=25, y=25)
        print(f"Contando... {i}")
        time.sleep(1)
    
    display.clear()
    display.show_text("Listo!", x=40, y=25)
    time.sleep(1)
    display.cleanup()


# ============================================================================
# EJEMPLO 5: Mostrar estadísticas de la cámara
# ============================================================================
def ejemplo_estadisticas_camara():
    """Captura frames y muestra estadísticas"""
    print("Ejecutando: Estadísticas de Cámara (10 segundos)")
    
    display = Display()
    camera = Camera()
    
    display.clear()
    display.show_text("Leyendo frames...", x=15, y=25)
    
    frame_count = 0
    start_time = time.time()
    
    for _ in range(300):  # Aproximadamente 10 segundos a 30 FPS
        frame = camera.get_frame()
        if frame is not None:
            frame_count += 1
        time.sleep(0.033)
    
    elapsed = time.time() - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    
    display.clear()
    display.show_multiline_text(
        f"Estadisticas\n"
        f"Frames: {frame_count}\n"
        f"Tiempo: {elapsed:.1f}s\n"
        f"FPS: {fps:.1f}",
        x=15, y=10, line_spacing=15
    )
    
    print(f"Frames capturados: {frame_count}")
    print(f"Tiempo: {elapsed:.1f}s")
    print(f"FPS: {fps:.1f}")
    
    time.sleep(3)
    display.cleanup()
    camera.cleanup()


# ============================================================================
# EJEMPLO 6: Grabar video
# ============================================================================
def ejemplo_grabar_video():
    """Graba video durante 10 segundos"""
    print("Ejecutando: Grabar Video (10 segundos)")
    
    display = Display()
    camera = Camera()
    
    timestamp = int(time.time())
    video_file = f"/home/pi/video_{timestamp}.h264"
    
    display.clear()
    display.show_text("Grabando...", x=30, y=25)
    
    if camera.start_recording(video_file):
        for i in range(10, 0, -1):
            display.clear()
            display.show_text(f"Grabando: {i}s", x=20, y=25)
            print(f"Grabando... {i}s")
            time.sleep(1)
        
        camera.stop_recording()
        display.clear()
        display.show_text("Video guardado!", x=15, y=25)
        print(f"Video guardado: {video_file}")
    else:
        display.clear()
        display.show_text("Error al grabar!", x=10, y=25)
        print("Error al grabar")
    
    time.sleep(3)
    display.cleanup()
    camera.cleanup()


# ============================================================================
# EJEMPLO 7: Mostrar menú interactivo
# ============================================================================
def ejemplo_menu():
    """Muestra un menú simple (sin interacción, solo visual)"""
    print("Ejecutando: Menú")
    
    display = Display()
    
    menu_items = [
        "1. Foto",
        "2. Video",
        "3. Mostrar Info",
        "4. Salir"
    ]
    
    display.clear()
    display.show_text("== MENU ==", x=35, y=5)
    
    y_pos = 20
    for item in menu_items:
        display.show_text(item, x=20, y=y_pos)
        y_pos += 12
    
    time.sleep(5)
    display.cleanup()


# ============================================================================
# EJEMPLO 8: Prueba de patrones
# ============================================================================
def ejemplo_patrones():
    """Muestra diferentes patrones en la pantalla"""
    print("Ejecutando: Patrones")
    
    display = Display()
    
    patrones = [
        "Patron 1\nLinea simple",
        "Patron 2\nDos lineas\nTres lineas",
        "Patron 3\nBorde izq  ",
        "Patron 4\nPrueba final",
    ]
    
    for patron in patrones:
        display.clear()
        display.show_multiline_text(patron, x=15, y=15, line_spacing=15)
        print(f"Mostrando: {patron.split(chr(10))[0]}")
        time.sleep(2)
    
    display.cleanup()


# ============================================================================
# SELECTOR DE EJEMPLOS
# ============================================================================
def main():
    """Menú principal para seleccionar ejemplos"""
    
    ejemplos = {
        '1': ('Hola Mundo', ejemplo_hola_mundo),
        '2': ('Información del Sistema', ejemplo_info_sistema),
        '3': ('Capturar Foto', ejemplo_capturar_foto),
        '4': ('Contador', ejemplo_contador),
        '5': ('Estadísticas de Cámara', ejemplo_estadisticas_camara),
        '6': ('Grabar Video', ejemplo_grabar_video),
        '7': ('Menú', ejemplo_menu),
        '8': ('Patrones', ejemplo_patrones),
    }
    
    print("\n" + "=" * 60)
    print("EJEMPLOS - Aplicación RPI Zero 2W")
    print("=" * 60)
    print("\nEjemplos disponibles:\n")
    
    for key, (nombre, _) in ejemplos.items():
        print(f"  {key}. {nombre}")
    
    print("\n  0. Salir")
    print("\n" + "=" * 60)
    
    while True:
        try:
            choice = input("\nSelecciona un ejemplo (0-8): ").strip()
            
            if choice == '0':
                print("Saliendo...")
                break
            
            if choice not in ejemplos:
                print("Opción inválida. Intenta de nuevo.")
                continue
            
            nombre, funcion = ejemplos[choice]
            print(f"\n>> Ejecutando: {nombre}\n")
            
            funcion()
            
            print(f">> {nombre} completado\n")
            
        except KeyboardInterrupt:
            print("\n\nInterrumpido por el usuario.")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
