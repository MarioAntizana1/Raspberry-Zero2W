#!/usr/bin/env python3
"""
Script Simple - Prueba Básica de Pantalla y Cámara
Ideal para verificar que todo está conectado correctamente
"""

import time
import sys

def test_display():
    """Prueba la pantalla OLED"""
    print("\n" + "=" * 60)
    print("PRUEBA 1: Pantalla OLED GMT020-02")
    print("=" * 60)
    
    try:
        from display import Display
        
        print("[INIT] Inicializando pantalla...")
        display = Display()
        
        print("[TEST] Mostrando 'Hola Mundo'...")
        display.clear()
        display.show_text("Hola Mundo", x=30, y=10)
        print("✓ Pantalla funcionando correctamente")
        
        time.sleep(2)
        
        print("[TEST] Mostrando múltiples líneas...")
        display.clear()
        display.show_multiline_text(
            "Prueba de\nPantalla OLED\nGMT020-02",
            x=15, y=15, line_spacing=15
        )
        print("✓ Texto multilínea funciona")
        
        time.sleep(2)
        
        print("[CLEANUP] Cerrando pantalla...")
        display.clear()
        display.cleanup()
        print("✓ Test de pantalla completado\n")
        return True
        
    except Exception as e:
        print(f"✗ Error en test de pantalla: {e}")
        return False


def test_camera():
    """Prueba la cámara"""
    print("=" * 60)
    print("PRUEBA 2: Cámara Raspberry Pi")
    print("=" * 60)
    
    try:
        from camera import Camera
        
        print("[INIT] Inicializando cámara...")
        camera = Camera()
        
        print("[TEST] Capturando foto de prueba...")
        photo_file = "/home/pi/test_photo.jpg"
        if camera.capture_photo(photo_file):
            print(f"✓ Foto capturada: {photo_file}")
        else:
            print("✗ No se pudo capturar la foto")
            return False
        
        print("[TEST] Obteniendo frames...")
        frames_captured = 0
        for i in range(30):
            frame = camera.get_frame()
            if frame is not None:
                frames_captured += 1
            time.sleep(0.033)
        
        print(f"✓ Frames capturados: {frames_captured}/30")
        
        print("[CLEANUP] Cerrando cámara...")
        camera.cleanup()
        print("✓ Test de cámara completado\n")
        return True
        
    except Exception as e:
        print(f"✗ Error en test de cámara: {e}")
        return False


def test_integration():
    """Prueba integrada de pantalla y cámara"""
    print("=" * 60)
    print("PRUEBA 3: Integración Pantalla + Cámara")
    print("=" * 60)
    
    try:
        from display import Display
        from camera import Camera
        
        display = Display()
        camera = Camera()
        
        print("[TEST] Mostrando datos en vivo...")
        display.clear()
        display.show_text("Hola Mundo", x=30, y=10)
        display.show_text("Camara Activa", x=20, y=30)
        display.show_text("Test: OK", x=40, y=50)
        
        for i in range(5):
            frame = camera.get_frame()
            if frame is not None:
                print(f"  Frame {i+1}/5 capturado - Shape: {frame.shape}")
            time.sleep(0.5)
        
        print("✓ Integración funciona correctamente")
        
        display.cleanup()
        camera.cleanup()
        print("✓ Test de integración completado\n")
        return True
        
    except Exception as e:
        print(f"✗ Error en test de integración: {e}")
        return False


def main():
    """Ejecuta todas las pruebas"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Pruebas de Hardware - Raspberry Pi Zero 2W".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = []
    
    # Test de pantalla
    results.append(("Pantalla OLED", test_display()))
    time.sleep(1)
    
    # Test de cámara
    results.append(("Cámara", test_camera()))
    time.sleep(1)
    
    # Test de integración
    results.append(("Integración", test_integration()))
    
    # Resumen
    print("=" * 60)
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASÓ" if passed else "✗ FALLÓ"
        print(f"{name:<30} {status}")
    
    all_passed = all(result[1] for result in results)
    print("=" * 60)
    
    if all_passed:
        print("\n✓ TODAS LAS PRUEBAS PASARON - Sistema listo para usar")
        print("\nEjecuta: python3 main.py\n")
    else:
        print("\n✗ ALGUNAS PRUEBAS FALLARON - Revisa las conexiones")
        print("Consulta el README.md para solucionar problemas\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
