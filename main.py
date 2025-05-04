import os
import discord
from discord.ext import commands
import asyncio
from PIL import Image, ImageOps
import io
from flask import Flask
from threading import Thread

# Configuração do servidor web para manter o bot online
app = Flask('')

@app.route('/')
def home():
    return "Bot está online!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
prefixos = [".", ". ", "oi ", "Oi "]
bot = commands.Bot(command_prefix=prefixos, intents=intents)

SERVIDOR_ID = 541806279232978978
CANAL_ID = 736438068206108742

def transformar_imagem(img, tema):
    try:
        img = img.convert("RGBA")
        if tema.startswith("Vet"):
            tipo_borda = "branco"
        else:
            tipo_borda = "transparente"

        largura, altura = img.size
        if largura != altura:
            tamanho_maximo = max(largura, altura)
            delta_largura = tamanho_maximo - largura
            delta_altura = tamanho_maximo - altura
            borda_esquerda = delta_largura // 2
            borda_direita = delta_largura - borda_esquerda
            borda_topo = delta_altura // 2
            borda_baixo = delta_altura - borda_topo

            if tipo_borda == "branco":
                cor_borda = (255, 255, 255, 255)
            else:
                cor_borda = (0, 0, 0, 0)

            img = ImageOps.expand(img, border=(borda_esquerda, borda_topo, borda_direita, borda_baixo), fill=cor_borda)
        return img
    except Exception as e:
        print(f"Erro ao processar imagem: {e}")
        return None

async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Cog {filename} carregado com sucesso!')
            except Exception as e:
                print(f'Erro ao carregar o cog {filename}: {e}')

async def enviar_mensagem_periodica():
    """Envia uma mensagem periodicamente com retry."""
    guild = bot.get_guild(SERVIDOR_ID)
    if not guild:
        print(f"Servidor com ID {SERVIDOR_ID} não encontrado.")
        return

    channel = guild.get_channel(CANAL_ID)
    if not channel:
        print(f"Canal com ID {CANAL_ID} não encontrado no servidor.")
        return

    max_retries = 5  # Número máximo de tentativas
    retry_delay = 1  # Tempo inicial de espera (segundos)

    while True:
        for attempt in range(max_retries):
            try:
                await channel.send("Estou online!")
                print("Mensagem 'Estou online!' enviada com sucesso.")
                break  # Sai do loop de tentativas se a mensagem for enviada
            except discord.errors.HTTPException as e:
                print(f"Erro ao enviar mensagem (HTTPException - tentativa {attempt + 1}/{max_retries}): {e}")
            except discord.errors.ConnectionClosed as e:
                print(f"Conexão fechada (tentativa {attempt + 1}/{max_retries}): {e}")
                # Possível lógica para reconectar o bot aqui, se necessário
            except asyncio.TimeoutError as e:
                print(f"Timeout ao enviar mensagem (tentativa {attempt + 1}/{max_retries}): {e}")
            except Exception as e:
                print(f"Erro inesperado ao enviar mensagem (tentativa {attempt + 1}/{max_retries}): {e}")

            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Backoff exponencial
            else:
                print("Número máximo de tentativas atingido. Falha ao enviar a mensagem.")
                # Opcional: Enviar uma mensagem de alerta para você mesmo ou registrar o erro
                # await bot.get_user(SEU_ID).send("Alerta: Falha ao enviar mensagem periódica.")

        await asyncio.sleep(30)  # Intervalo entre envios (30 segundos)

@bot.event
async def on_ready():
    print(f'Bot está online como {bot.user.name}')
    print('------')

    await load_extensions()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

    bot.loop.create_task(enviar_mensagem_periodica())

@bot.command()
async def ajuda(ctx):
    await ctx.send("""
**Comandos disponíveis:**
`!ajuda` - Exibe esta mensagem de ajuda
`!quadrificar [tema]` - Transforma uma imagem anexada em uma imagem quadrada (anexe uma imagem junto com o comando)
    Temas disponíveis: Veterinária (bordas brancas), Outros (bordas transparentes)
    """)

@bot.command()
async def quadrificar(ctx, tema="Outros"):
    if len(ctx.message.attachments) == 0:
        await ctx.send("Por favor, anexe uma imagem junto com o comando.")
        return

    imagem_anexada = ctx.message.attachments[0]
    if not imagem_anexada.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        await ctx.send("O arquivo anexado não é uma imagem válida.")
        return

    imagem_bytes = await imagem_anexada.read()
    imagem_original = Image.open(io.BytesIO(imagem_bytes))

    await ctx.send(f"Processando imagem com tema '{tema}'...")
    imagem_processada = transformar_imagem(imagem_original, tema)

    if imagem_processada:
        buffer = io.BytesIO()
        imagem_processada.save(buffer, format='PNG')
        buffer.seek(0)

        await ctx.send(f"Aqui está sua imagem quadrificada:", file=discord.File(buffer, filename=f"quadrificado_{imagem_anexada.filename.split('.')[0]}.png"))
    else:
        await ctx.send("Houve um erro ao processar a imagem.")

keep_alive()

if __name__ == "__main__":
    token = os.environ.get('discord_token')
    if not token:
        print("ERRO: Variável de ambiente discord_token não configurada!")
    else:
        bot.run(token)
