import os
import discord
from discord.ext import commands
import boto3
from dotenv import load_dotenv
import asyncio
import random
from keep_alive import keep_alive



# Cargar variables de entorno
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
REGION = 'us-east-1'
INSTANCE_ID = os.getenv('INSTANCE_ID')

# Configurar conexión con AWS
ec2 = boto3.client('ec2', 
                   region_name=REGION,
                   aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
                   aws_secret_access_key=os.getenv('AWS_SECRET_KEY'))

# Configurar el Bot de Discord con los permisos (Intents)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado exitosamente como {bot.user}')

@bot.command(name='prender')
async def prender_server(ctx):
    # Aviso inicial de que el proceso es largo
    await ctx.send("⏳ Contactando a Pablo... Iniciando el Rape Mode.\n⚠️ 5 minutos tarda en encender el server ")
    
    try:
        # 1. Mandar a encender la instancia
        ec2.start_instances(InstanceIds=[INSTANCE_ID])
        await ctx.send("✅ Instancia iniciada. Obteniendo IP")
        
        # 2. Esperar 5 segundos para la IP
        await asyncio.sleep(5)
        
        response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
        ip_publica = response['Reservations'][0]['Instances'][0].get('PublicIpAddress')
        
        if ip_publica:
            await ctx.send(f"🌐 IP obtenida: `{ip_publica}` recordadr que hay que cambiar la ip cada vez que se inicie el servidor\n⏳ Me quedaré esperando el resto del tiempo de carga. Te avisaré apenas pasen los 6:30 min.")
        else:
            await ctx.send("⚠️ AWS aún no suelta la IP, pero el servidor sigue cargando. Avisaré al terminar los 6:30 min.")

        # 3. Esperar el resto del tiempo para completar los 6:30 min (390 segundos)
        # Como ya esperamos 15, restamos: 390 - 15 = 375 segundos
        await asyncio.sleep(285)
        
        # 4. Aviso final de servidor listo con imagen desde GitHub
        mencion = "@everyone" # Puedes cambiar esto por un rol si prefieres
        
        # Usamos el enlace RAW de GitHub para que Discord pueda renderizar la imagen
        url_imagen_github = "https://raw.githubusercontent.com/ttvgestapo-dev/imagenes-bot/main/WhatsApp%20Image%202026-05-14%20at%209.17.17%20AM.jpeg"
        
        # Creamos el diseño visual (Embed)
        embed = discord.Embed(
            title="🔥 ¡EL SERVIDOR ESTA LISTO!",
            description=f"{mencion} **¡TODOS A VIOLAR!**",
            color=discord.Color.dark_red() # Color de la barrita lateral
        )
        embed.set_image(url=url_imagen_github)
        
        # Enviamos el aviso final con la imagen incorporada
        await ctx.send(embed=embed)
            
    except Exception as e:
        await ctx.send(f"❌ Error al iniciar: {e}")

@bot.command(name='apagar')
async def apagar_server(ctx):
    await ctx.send("⏳ Apagando el servidor, Pablo no contesto...")
    try:
        # 1. Mandar a apagar la instancia
        ec2.stop_instances(InstanceIds=[INSTANCE_ID])
        
        # 2. Enlaces RAW de GitHub (vital para que Discord renderice la foto)
        url_img1 = "https://raw.githubusercontent.com/ttvgestapo-dev/imagenes-bot/main/WhatsApp%20Image%202026-05-14%20at%209.39.59%20AM.jpeg"
        url_img2 = "https://raw.githubusercontent.com/ttvgestapo-dev/imagenes-bot/main/WhatsApp%20Image%202026-05-14%20at%209.38.35%20AM.jpeg"
        
        # 3. Creamos el primer diseño (Embed) con el texto y la primera imagen
        embed1 = discord.Embed(
            title="💤 Servidor apagado.",
            description="**¡Alguien sera violado!**",
            color=discord.Color.dark_gray() # Color gris para indicar que está apagado
        )
        embed1.set_image(url=url_img1)
        
        # 4. Creamos el segundo diseño (Embed) que solo contendrá la segunda imagen
        embed2 = discord.Embed(
            color=discord.Color.dark_gray()
        )
        embed2.set_image(url=url_img2)
        
        # 5. Enviamos ambos embeds de una sola vez usando el parámetro 'embeds' (en plural)
        await ctx.send(embeds=[embed1, embed2])
        
    except Exception as e:
        await ctx.send(f"❌ Error al apagar: {e}")

@bot.command(name='estado')
async def estado_server(ctx):
    try:
        response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
        estado = response['Reservations'][0]['Instances'][0]['State']['Name']
        
        # Le damos un poco de formato visual dependiendo del estado
        if estado == 'running':
            mensaje = "🟢 El servidor está **CUCKEANDO** mientras Dieguito está en la Muni sentado haciendo **NADA!!**!"
        elif estado == 'stopped':
            mensaje = "🔴 El servidor está **APAGADO** y dieguito fue violado!!."
        elif estado == 'pending':
            mensaje = "🟡 El servidor se está encendiendo en este momento."
        elif estado == 'stopping':
            mensaje = "🟡 El servidor se está apagando."
        else:
            mensaje = f"⚪ Estado actual: {estado}"
            
        await ctx.send(mensaje)
    except Exception as e:
        await ctx.send(f"❌ Error al consultar estado: {e}")

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

# Mantener vivo el bot en Azure App Service (plan F1)
keep_alive()

# Iniciar el bot
bot.run(DISCORD_TOKEN)