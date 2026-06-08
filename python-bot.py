import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import random
from keep_alive import keep_alive
import azure_vm
import ssh_manager


# Cargar variables de entorno
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Configurar el Bot de Discord con los permisos (Intents)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


# ══════════════════════════════════════════════════════════════════════════════
#  Vista interactiva con botones para elegir modpack
# ══════════════════════════════════════════════════════════════════════════════

class ModpackView(discord.ui.View):
    """
    Vista con dos botones: ATM 10 (verde) y Cursed Walking (rojo).
    Al hacer clic, ejecuta la secuencia SSH: stop → esperar → start.
    """

    def __init__(self, vm_ip: str, channel):
        super().__init__(timeout=120)  # 2 minutos para elegir
        self.vm_ip = vm_ip
        self.channel = channel  # Canal donde enviar mensajes nuevos

    async def _launch_modpack(self, interaction: discord.Interaction, modpack_name: str):
        """Lógica compartida por ambos botones: detener, esperar, iniciar."""

        # 1. Deshabilitar botones para evitar doble clic
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content=f"✅ **{interaction.user.display_name}** eligió **{modpack_name}**.",
            view=self
        )

        try:
            # 2. Paso A — Apagar seguro: enviar 'stop' a la consola de Minecraft
            await self.channel.send(f"🍆 Deteniendo servidor anterior (si hay alguno)...")
            await asyncio.to_thread(ssh_manager.stop_minecraft_server, self.vm_ip)

            # 3. Paso B — Esperar 10s para que Java guarde chunks y mundo
            await self.channel.send("⏳ Esperando 10s para que Java guarde los chunks...")
            await asyncio.sleep(10)

            # 4. Paso C — Iniciar el modpack elegido en una nueva sesión de screen
            await self.channel.send(f"🚀🍑🍆 Lanzando **{modpack_name}**...")
            await asyncio.to_thread(ssh_manager.start_modpack, self.vm_ip, modpack_name)

            # 5. Confirmación final con embed visual + imagen
            # URL de imagen para cuando el modpack se lanza (cambia esta URL por la que quieras)
            url_img_modpack = "https://raw.githubusercontent.com/puntodev90-dev/images/refs/heads/main/WhatsApp%20Image%202026-05-14%20at%209.17.17%20AM.jpeg"

            embed = discord.Embed(
                title=f"🚀 Iniciando  {modpack_name}",
                description=(
                    f"Dame un par de minutos para cargar PENTAHO.....\n\n"
                    f"**IP:** `{self.vm_ip}:25565`"
                ),
                color=discord.Color.green()
            )
            embed.set_image(url=url_img_modpack)
            embed.set_footer(text=f"Solicitado por {interaction.user.display_name}")

            await self.channel.send(embed=embed)

        except Exception as e:
            await self.channel.send(f"❌ Error al iniciar **{modpack_name}**: `{e}`")

    @discord.ui.button(label="ATM 10", style=discord.ButtonStyle.green, emoji="🍑")
    async def atm10_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._launch_modpack(interaction, "ATM 10")

    @discord.ui.button(label="Cursed Walking", style=discord.ButtonStyle.red, emoji="🍆")
    async def cursed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._launch_modpack(interaction, "Cursed Walking")

    async def on_timeout(self):
        """Si nadie elige en 2 minutos, deshabilitar los botones."""
        for child in self.children:
            child.disabled = True


# ══════════════════════════════════════════════════════════════════════════════
#  Eventos del bot
# ══════════════════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f'Bot conectado exitosamente como {bot.user}')


# ══════════════════════════════════════════════════════════════════════════════
#  Comando: !prender — Enciende la VM de Azure + elige modpack
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name='prender')
async def prender_server(ctx):
    """Enciende la VM en Azure, obtiene la IP, y presenta los botones de modpack."""

    await ctx.send("⏳ Despertando la máquina en Azure🍑🍆🍑🍆🍑🍆🍑🍆...")

    try:
        # 1. Enviar comando de encendido (fire-and-forget, no espera)
        await asyncio.to_thread(azure_vm.start_vm)
        await ctx.send("✅🍑🍆 Comando de encendido enviado a Azure y despertando a dieguito.")

        # 2. Pollear el estado cada 10s hasta que esté 'running'
        vm_encendida = False
        for _ in range(24):  # Máximo ~4 minutos
            await asyncio.sleep(10)
            estado = await asyncio.to_thread(azure_vm.get_vm_status)
            if estado == 'running':
                vm_encendida = True
                break
        
        if not vm_encendida:
            await ctx.send("⚠️ La VM está tardando más de lo esperado. Usa `!estado` para verificar.")
            return

        await ctx.send("✅ ¡La máquina está encendida!")

        # 3. Obtener IP pública con reintentos (puede tardar unos segundos en asignarse)
        vm_ip = None
        last_error = None
        for intento in range(8):  # 8 intentos x 5s = 40s máximo
            try:
                vm_ip = await asyncio.to_thread(azure_vm.get_vm_ip)
            except Exception as ip_err:
                last_error = ip_err
            if vm_ip:
                break
            await asyncio.sleep(5)

        if not vm_ip:
            error_detail = f"\nError: `{last_error}`" if last_error else ""
            await ctx.send(f"⚠️ No se pudo obtener la IP pública.{error_detail}")
            return

        await ctx.send(f"🌐 IP obtenida: `{vm_ip}:25565`")

        # 4. Esperar a que SSH esté listo
        await asyncio.sleep(10)

        # 5. Mostrar botones de selección de modpack
        view = ModpackView(vm_ip, ctx.channel)
        await ctx.send("🎮 **¿Qué modpack deseas jugar, bestia?**", view=view)

    except Exception as e:
        await ctx.send(f"❌ Error al encender la VM: `{e}`")


# ══════════════════════════════════════════════════════════════════════════════
#  Comando: !apagar — Detiene Minecraft + desasigna la VM (frena cobros)
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name='apagar')
async def apagar_server(ctx):
    """Envía 'stop' por SSH, espera, y luego desasigna la VM para frenar los cobros."""

    await ctx.send("⏳ Apagando el servidor de Minecraft...")

    try:
        # 1. Obtener la IP para conectarse por SSH
        vm_ip = await asyncio.to_thread(azure_vm.get_vm_ip)

        if vm_ip:
            # 2. Enviar 'stop' a la consola de Minecraft
            await asyncio.to_thread(ssh_manager.stop_minecraft_server, vm_ip)
            await ctx.send("🛑 Comando `stop` enviado a Minecraft. Esperando 15s para guardar chunks...")

            # 3. Darle tiempo a Java para guardar el mundo
            await asyncio.sleep(15)

        # 4. Enviar comando de desasignación (fire-and-forget)
        await ctx.send("💤 Desasignando la VM en Azure...")
        await asyncio.to_thread(azure_vm.deallocate_vm)

        # 5. Pollear hasta que esté desasignada
        vm_apagada = False
        for _ in range(18):  # Máximo ~3 minutos
            await asyncio.sleep(10)
            estado = await asyncio.to_thread(azure_vm.get_vm_status)
            if estado == 'deallocated':
                vm_apagada = True
                break

        if not vm_apagada:
            await ctx.send("⚠️ La desasignación está tardando. Usa `!estado` para verificar.")
            return

        # 6. Confirmación visual con embeds e imágenes
        embed1 = discord.Embed(
            title="💤 Servidor apagado y desasignado.",
            description="**La VM ha sido desasignada. No se generan cobros.**",
            color=discord.Color.dark_gray()
        )

        url_img1 = "https://raw.githubusercontent.com/puntodev90-dev/images/refs/heads/main/WhatsApp%20Image%202026-05-14%20at%209.38.35%20AM.jpeg"
        url_img2 = "https://raw.githubusercontent.com/puntodev90-dev/images/refs/heads/main/WhatsApp%20Image%202026-06-08%20at%201.18.28%20AM%20(2).jpeg"

        embed1.set_image(url=url_img1)

        embed2 = discord.Embed(color=discord.Color.dark_gray())
        embed2.set_image(url=url_img2)

        await ctx.send(embeds=[embed1, embed2])

    except Exception as e:
        await ctx.send(f"❌ Error al apagar: `{e}`")


# ══════════════════════════════════════════════════════════════════════════════
#  Comando: !estado — Consulta el estado de la VM en Azure
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name='estado')
async def estado_server(ctx):
    """Consulta el estado actual de la VM en Azure."""
    try:
        estado = await asyncio.to_thread(azure_vm.get_vm_status)

        if estado == 'running':
            try:
                vm_ip = await asyncio.to_thread(azure_vm.get_vm_ip)
            except Exception as ip_err:
                vm_ip = None
                print(f"[!estado] Error obteniendo IP: {ip_err}")
            ip_text = f"\n🌐 IP: `{vm_ip}:25565`" if vm_ip else "\n⚠️ No se pudo obtener la IP."
            mensaje = f"🟢 La VM está **ENCENDIDA** y corriendo.{ip_text}"
        elif estado == 'deallocated':
            mensaje = "🔴 La VM está **DESASIGNADA** (apagada, sin cobros)."
        elif estado == 'starting':
            mensaje = "🟡 La VM se está **encendiendo** en este momento."
        elif estado in ('stopping', 'deallocating'):
            mensaje = "🟡 La VM se está **apagando/desasignando**."
        elif estado == 'stopped':
            mensaje = (
                "🟠 La VM está **detenida** pero aún asignada (puede generar cobros).\n"
                "Usa `!apagar` para desasignar completamente."
            )
        else:
            mensaje = f"⚪ Estado actual de la VM: `{estado}`"

        await ctx.send(mensaje)
    except Exception as e:
        await ctx.send(f"❌ Error al consultar estado: `{e}`")


# ══════════════════════════════════════════════════════════════════════════════
#  Comando: !Cp — Imagen random (preservado sin cambios)
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name='Cp')
async def imagen_random(ctx):
    await ctx.send("👀 Accediendo a la base de datos de **PABLO**... 👀")

    # Tu array (lista) con los links ya definidos
    # Asegúrate de que los links terminen en .jpg, .png o .gif para que Discord los muestre bien
    lista_imagenes = [
        "https://thumb-cdn77.xvideos-cdn.com/dbfacb14-52b3-4c0e-83b8-cff0ed3c6f79/0/xv_30_p.jpg",
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS9q6JQopQ1By56oxrZw9EFrfbRBccCVZiZCQ&s",
        "https://thumb-cdn77.xvideos-cdn.com/7340a5fd-1b86-4c72-b516-8f387d35fdd8/0/xv_30_p.jpg",
        "https://www.xleche.com/wp-content/uploads/2025/04/Mia-K-Video-porn-XXX.webp",
        "https://ejemplo.com/imagen5.jpg",
        "https://thumb-cdn77.xvideos-cdn.com/ffd92193-1227-416e-8b13-cb61f0dd23b1/0/xv_30_p.jpg",
        "https://ei.phncdn.com/videos/202309/08/439030961/original/(m=q7SRX3YbeaSaaTbaAaaaa)(mh=Afm9lCqbyrGjieHZ)0.jpg",
        "https://ei.phncdn.com/videos/201903/20/214077662/original/(m=qUQ2LZYbeaSaaTbaAaaaa)(mh=LPs0VCmi_NSnTkqo)0.jpg",
        "https://media.thisvid.com/contents/videos_screenshots/11607000/11607397/preview.jpg",
        "https://media.tenor.com/cYCZH_WGX6gAAAAe/vardoc1-cuck.png"
    ]

    try:
        # La magia de Python: elige un elemento al azar de la lista
        url_elegida = random.choice(lista_imagenes)

        # Armamos el mensaje visual
        embed = discord.Embed(
            title="🔥 Happy Chantussy",
            color=discord.Color.dark_red()
        )
        embed.set_image(url=url_elegida)

        # Enviamos la imagen al canal
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Error al enviar la imagen: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  Comando: !Pape — Muestra imagen de Pape
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name='Pape')
async def imagen_pape(ctx):
    """Muestra la imagen de Pape desde GitHub."""
    try:
        # Cambia esta URL por la imagen real de Pape (enlace RAW de GitHub)
        url_pape = "https://raw.githubusercontent.com/puntodev90-dev/images/refs/heads/main/WhatsApp%20Image%202026-06-08%20at%201.18.27%20AM.jpeg"

        embed = discord.Embed(
            title="🔥 Pape",
            color=discord.Color.purple()
        )
        embed.set_image(url=url_pape)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Error al enviar la imagen: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  Comando: !Ikkyi — Muestra imagen de Ikkyi
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name='Ikkyi')
async def imagen_ikkyi(ctx):
    """Muestra la imagen de Ikkyi desde GitHub."""
    try:
        # Cambia esta URL por la imagen real de Ikkyi (enlace RAW de GitHub)
        url_ikkyi = "https://raw.githubusercontent.com/puntodev90-dev/images/refs/heads/main/WhatsApp%20Image%202026-06-08%20at%201.18.28%20AM%20(1).jpeg"

        embed = discord.Embed(
            title="🔥 Ikkyi",
            color=discord.Color.dark_red()
        )
        embed.set_image(url=url_ikkyi)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Error al enviar la imagen: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  Arranque del bot
# ══════════════════════════════════════════════════════════════════════════════

# Mantener vivo el bot en Azure App Service (plan F1)
keep_alive()

# Iniciar el bot
bot.run(DISCORD_TOKEN)