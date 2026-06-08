"""
azure_vm.py - Módulo para gestionar la VM de Azure (encender, desasignar, consultar IP/estado).

Usa el SDK de Azure con autenticación por Service Principal (ClientSecretCredential).
Todas las funciones son SÍNCRONAS; el bot las ejecuta con asyncio.to_thread()
para no bloquear el event loop de Discord.
"""

import os
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient


# ── Configuración desde variables de entorno ──────────────────────────────────
TENANT_ID = os.getenv('AZURE_TENANT_ID')
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
RESOURCE_GROUP = os.getenv('AZURE_RESOURCE_GROUP')
VM_NAME = os.getenv('AZURE_VM_NAME')

# ── Autenticación con Service Principal ───────────────────────────────────────
credential = ClientSecretCredential(
    tenant_id=TENANT_ID,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)

# ── Clientes del SDK de Azure ─────────────────────────────────────────────────
compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credential, SUBSCRIPTION_ID)


def _parse_resource_id(resource_id):
    """
    Extrae (resource_group, nombre) de un Azure Resource ID completo.
    Formato: /subscriptions/.../resourceGroups/MI-RG/providers/.../nombre
    Esto es más robusto que asumir que todo está en el mismo Resource Group.
    """
    parts = resource_id.split('/')
    rg_index = next(i for i, p in enumerate(parts) if p.lower() == 'resourcegroups')
    return parts[rg_index + 1], parts[-1]


def start_vm():
    """
    Envía el comando de encendido a Azure.
    NO espera a que termine — el bot polleará get_vm_status() por su cuenta.
    Esto evita bloquear 1-2 minutos sin dar feedback al usuario.
    """
    compute_client.virtual_machines.begin_start(RESOURCE_GROUP, VM_NAME)


def deallocate_vm():
    """
    Envía el comando de desasignación a Azure.
    NO espera a que termine — el bot polleará get_vm_status() por su cuenta.
    """
    compute_client.virtual_machines.begin_deallocate(RESOURCE_GROUP, VM_NAME)


def get_vm_ip():
    """
    Obtiene la IP pública de la VM.
    Usa dos métodos por robustez: si uno falla, intenta el otro.
    Imprime errores reales en consola para diagnóstico.
    """

    # ── Método 1 (más simple): listar todas las IPs públicas del Resource Group ──
    try:
        for pip in network_client.public_ip_addresses.list(RESOURCE_GROUP):
            if pip.ip_address:
                print(f"[get_vm_ip] IP encontrada (método 1): {pip.ip_address}")
                return pip.ip_address
    except Exception as e:
        print(f"[get_vm_ip] Método 1 (listar IPs) falló: {e}")

    # ── Método 2 (navegación): VM → NIC → IP Configuration → Public IP ──
    try:
        vm = compute_client.virtual_machines.get(RESOURCE_GROUP, VM_NAME)
        nic_id = vm.network_profile.network_interfaces[0].id
        nic_rg, nic_name = _parse_resource_id(nic_id)

        nic = network_client.network_interfaces.get(nic_rg, nic_name)

        if not nic.ip_configurations:
            print("[get_vm_ip] Método 2: la NIC no tiene ip_configurations")
            return None

        public_ip_ref = nic.ip_configurations[0].public_ip_address

        if not public_ip_ref:
            print("[get_vm_ip] Método 2: no hay public_ip_address en la ip_configuration")
            return None

        pip_rg, pip_name = _parse_resource_id(public_ip_ref.id)
        public_ip = network_client.public_ip_addresses.get(pip_rg, pip_name)
        print(f"[get_vm_ip] IP encontrada (método 2): {public_ip.ip_address}")
        return public_ip.ip_address
    except Exception as e:
        print(f"[get_vm_ip] Método 2 (navegación) falló: {e}")

    return None


def get_vm_status():
    """
    Consulta el estado de energía de la VM.
    Retorna: 'running', 'deallocated', 'stopped', 'starting', 'stopping', etc.
    """
    try:
        instance_view = compute_client.virtual_machines.instance_view(
            RESOURCE_GROUP, VM_NAME
        )
        for status in instance_view.statuses:
            if status.code.startswith('PowerState/'):
                return status.code.split('/')[-1]
        return 'unknown'
    except Exception as e:
        return f'error: {e}'
