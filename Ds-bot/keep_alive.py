"""
keep_alive.py - Servidor web ligero para evitar la hibernación en Azure App Service (Plan F1).

Levanta un servidor Flask en un hilo secundario que responde en el puerto 8000.
Azure (o un servicio externo como UptimeRobot) puede hacer ping a la ruta '/'
para mantener la aplicación activa y evitar que el plan gratuito la detenga por inactividad.
"""

from flask import Flask
from threading import Thread

app = Flask(__name__)


@app.route('/')
def home():
    return 'Bot activo', 200


def keep_alive():
    """Inicia el servidor Flask en un hilo secundario para no bloquear el event loop del bot."""
    thread = Thread(target=lambda: app.run(host='0.0.0.0', port=8000), daemon=True)
    thread.start()
