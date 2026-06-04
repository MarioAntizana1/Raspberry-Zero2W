"""
Módulo para controlar la cámara de la Raspberry Pi
Soporta captura de fotos y video
"""

import time
from picamera2 import Picamera2
from config import CAMERA_CONFIG, DEBUG

class Camera:
    def __init__(self):
        """Inicializa la cámara"""
        self.camera = None
        self.is_recording = False
        self._init_camera()
    
    def _init_camera(self):
        """Inicializa la conexión con la cámara"""
        try:
            self.camera = Picamera2()
            
            # Configurar resolución
            config = self.camera.create_video_configuration(
                main={"size": CAMERA_CONFIG['resolution']},
                raw={"size": self.camera.sensor_resolution}
            )
            self.camera.configure(config)
            
            # Iniciar cámara
            self.camera.start()
            
            # Esperar a que se estabilice
            time.sleep(2)
            
            if DEBUG:
                print("[CAMERA] Cámara inicializada correctamente")
                print(f"[CAMERA] Resolución: {CAMERA_CONFIG['resolution']}")
                print(f"[CAMERA] FPS: {CAMERA_CONFIG['framerate']}")
                
        except Exception as e:
            print(f"[ERROR] Error al inicializar la cámara: {e}")
            raise
    
    def capture_photo(self, filename):
        """
        Captura una foto
        
        Args:
            filename: Nombre del archivo para guardar la foto
            
        Returns:
            bool: True si la captura fue exitosa, False en caso contrario
        """
        try:
            if not self.camera:
                print("[ERROR] Cámara no inicializada")
                return False
            
            self.camera.capture_file(filename)
            
            if DEBUG:
                print(f"[CAMERA] Foto capturada: {filename}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error al capturar foto: {e}")
            return False
    
    def start_recording(self, filename):
        """
        Inicia la grabación de video
        
        Args:
            filename: Nombre del archivo para guardar el video
            
        Returns:
            bool: True si la grabación inició correctamente
        """
        try:
            if not self.camera:
                print("[ERROR] Cámara no inicializada")
                return False
            
            if self.is_recording:
                print("[ADVERTENCIA] Grabación ya en curso")
                return False
            
            self.camera.start_recording('h264', filename)
            self.is_recording = True
            
            if DEBUG:
                print(f"[CAMERA] Grabación iniciada: {filename}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error al iniciar grabación: {e}")
            return False
    
    def stop_recording(self):
        """
        Detiene la grabación de video
        
        Returns:
            bool: True si la grabación se detuvo correctamente
        """
        try:
            if not self.camera or not self.is_recording:
                print("[ADVERTENCIA] No hay grabación activa")
                return False
            
            self.camera.stop_recording()
            self.is_recording = False
            
            if DEBUG:
                print("[CAMERA] Grabación detenida")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error al detener grabación: {e}")
            return False
    
    def get_frame(self):
        """
        Obtiene el frame actual de la cámara
        
        Returns:
            numpy.ndarray: Array con los datos de la imagen
        """
        try:
            if not self.camera:
                print("[ERROR] Cámara no inicializada")
                return None
            
            frame = self.camera.capture_array()
            return frame
            
        except Exception as e:
            print(f"[ERROR] Error al obtener frame: {e}")
            return None
    
    def cleanup(self):
        """Limpia los recursos de la cámara"""
        try:
            if self.camera:
                if self.is_recording:
                    self.stop_recording()
                self.camera.close()
                if DEBUG:
                    print("[CAMERA] Cámara cerrada")
        except Exception as e:
            print(f"[ERROR] Error al cerrar cámara: {e}")
