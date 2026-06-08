"""
ssh_manager.py - Módulo para ejecutar comandos remotos por SSH en la VM de Azure.

Usa paramiko con autenticación por llave privada RSA (.pem).
Cada operación abre y cierra su propia conexión SSH para máxima robustez.
Funciones síncronas, diseñadas para llamarse con asyncio.to_thread().
"""

import os
import paramiko

# ── Configuración SSH desde variables de entorno ──────────────────────────────
SSH_USERNAME = os.getenv('SSH_USERNAME', 'azureuser')
SSH_KEY_PATH = os.getenv('SSH_KEY_PATH', 'mi_llave.pem')
SSH_PORT = 22

# ── Catálogo de modpacks: nombre → (directorio, script de arranque) ───────────
MODPACKS = {
    'ATM 10': {
        'path': '/minecraft/servidor_atm10',
        'script': './run.sh',
    },
    'Cursed Walking': {
        'path': '/minecraft/modpack_chantussy',
        'script': './start.sh',
    },
}


def _connect(ip):
    """Crea y retorna una conexión SSH autenticada con llave privada .pem."""
    key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=ip,
        port=SSH_PORT,
        username=SSH_USERNAME,
        pkey=key,
        timeout=15
    )
    return client


def run_ssh_command(ip, command):
    """Ejecuta un comando remoto por SSH. Retorna tupla (stdout, stderr)."""
    client = _connect(ip)
    try:
        _stdin, stdout, stderr = client.exec_command(command, timeout=30)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        return out, err
    finally:
        client.close()


def stop_minecraft_server(ip):
    """
    Envía el comando 'stop' a la consola de Minecraft dentro de la sesión de screen.
    screen interpreta \\n como un Enter, simulando que escribimos 'stop' + Enter.
    Si no hay sesión activa, el comando falla silenciosamente.
    """
    command = 'screen -S minecraft -X stuff "stop\\n"'
    return run_ssh_command(ip, command)


def start_modpack(ip, modpack_name):
    """
    Inicia el modpack especificado en una nueva sesión de screen llamada 'minecraft'.
    Lanza ValueError si el nombre del modpack no existe en el catálogo.
    """
    modpack = MODPACKS.get(modpack_name)
    if not modpack:
        raise ValueError(f"Modpack desconocido: {modpack_name}")

    command = f'cd {modpack["path"]} && screen -dmS minecraft {modpack["script"]}'
    return run_ssh_command(ip, command)
