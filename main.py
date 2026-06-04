#!/usr/bin/env python3
"""
Servidor web local para la cámara Raspberry Pi Zero 2W.
Elimina la pantalla y muestra video en el navegador.
"""

import io
import signal
import sys
from PIL import Image
from flask import Flask, Response, render_template_string
from camera import Camera
from config import DEBUG

app = Flask(__name__)

camera = None

HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Cámara RPi Zero 2W</title>
</head>
<body>
    <h1>Streaming de cámara Raspberry Pi</h1>
    <p>Accede al stream local en: <strong>/video_feed</strong></p>
    <img src="/video_feed" width="640" />
</body>
</html>
"""


def generate_frames():
    while True:
        frame = camera.get_frame()
        if frame is None:
            continue

        image = Image.fromarray(frame)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        buffer.seek(0)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.read() + b'\r\n')


@app.route('/')
def index():
    return render_template_string(HTML_PAGE)


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def cleanup():
    if camera:
        camera.cleanup()
        print('[INFO] Cámara cerrada')


def signal_handler(sig, frame):
    print('\n[INFO] Cerrando servidor...')
    cleanup()
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    try:
        print('Iniciando cámara...')
        camera = Camera()
        print('Cámara inicializada correctamente')
        print('Servidor web activo: http://0.0.0.0:5000')
        app.run(host='0.0.0.0', port=5000, threaded=True)
    except Exception as e:
        print(f'[ERROR] No se pudo iniciar la cámara o el servidor: {e}')
        cleanup()
        sys.exit(1)
