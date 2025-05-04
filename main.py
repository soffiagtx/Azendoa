import os
import discord
from discord.ext import commands
import asyncio  # Importe asyncio
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
    t.daemon = True  # Para que a thread se encerre quando o programa principal encerrar
    t.start()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
prefixos = [".", ". ", "oi ", "Oi "]
bot = commands.Bot(command_prefix=prefixos, intents=intents)

# ID do servidor e canal onde a mensagem será enviada (substitua pelos IDs reais)
SERVIDOR_ID = 541806279232978978  # Substitua pelo ID do seu servidor
CANAL_ID = 736438068206108742  # Substitua pelo ID do canal

# Função original de transformação de imagens, adaptada para trabalhar com arquivos em memória
def transformar_imagem(img, tema):
    try:
        # Converter para RGBA
        img = img.convert("RGBA")
        
        # Determinar tipo de borda baseado no tema
        if tema.startswith("Vet"):
            tipo_borda = "branco"
        else:
            tipo_borda = "transparente"
        
        largura, altura = img.size
        
        # Transformar em quadrado se necessário
        if largura != altura:
            tamanho_maximo = max(largura, altura)
            
            delta_largura = tamanho_maximo - largura
            delta_altura = tamanho_maximo - altura
            
            borda_esquerda = delta_largura // 2
            borda_direita = delta_largura - borda_esquerda
            borda_topo = delta_altura // 2
            borda_baixo = delta_altura - borda_topo
            
            if tipo_borda == "branco":
                cor_borda = (255, 255, 255, 255)  # Branco com alfa
            else:
                cor_borda = (0, 0, 0, 0)  # Transparente
            
            img = ImageOps.expand(img, border=(borda_esquerda, borda_topo, borda_direita, borda_baixo), fill=cor_borda)
        
        # Retorna a imagem processada
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
    """Envia uma mensagem periodicamente para manter o bot ativo."""
    guild = bot.get_guild(SERVIDOR_ID)  # Obtém o servidor pelo ID
    if guild:
        canal = guild.get_channel(CANAL_ID)  # Obtém o canal pelo ID
        if canal:
            while True:
                try:
                    await canal.send("Estou online!")  # Envia a mensagem
                    await asyncio.sleep(30)  # Espera 30 segundos
                except Exception as e:
                    print(f"Erro ao enviar mensagem periódica: {e}")
                    await asyncio.sleep(60)  # Espera 1 minuto para tentar novamente
        else:
            print(f"Canal com ID {CANAL_ID} não encontrado no servidor.")
    else:
        print(f"Servidor com ID {SERVIDOR_ID} não encontrado.")

@bot.event
async def on_ready():
    print(f'Bot está online como {bot.user.name}')
    print('------')

    await load_extensions()  # carrega as extensões
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    
    bot.loop.create_task(enviar_mensagem_periodica())  # Inicia a tarefa

@bot.command()
async def ajuda(ctx):
    """Exibe os comandos disponíveis"""
    await ctx.send("""
**Comandos disponíveis:**
`!ajuda` - Exibe esta mensagem de ajuda
`!quadrificar [tema]` - Transforma uma imagem anexada em uma imagem quadrada (anexe uma imagem junto com o comando)
    Temas disponíveis: Veterinária (bordas brancas), Outros (bordas transparentes)
    """)

@bot.command()
async def quadrificar(ctx, tema="Outros"):
    """Transforma uma imagem anexada em uma imagem quadrada"""
    # Verificar se uma imagem foi anexada
    if len(ctx.message.attachments) == 0:
        await ctx.send("Por favor, anexe uma imagem junto com o comando.")
        return
    
    # Obter a primeira imagem anexada
    imagem_anexada = ctx.message.attachments[0]
    
    # Verificar se é realmente uma imagem
    if not imagem_anexada.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        await ctx.send("O arquivo anexado não é uma imagem válida.")
        return
    
    # Baixar a imagem
    imagem_bytes = await imagem_anexada.read()
    imagem_original = Image.open(io.BytesIO(imagem_bytes))
    
    # Transformar a imagem
    await ctx.send(f"Processando imagem com tema '{tema}'...")
    imagem_processada = transformar_imagem(imagem_original, tema)
    
    if imagem_processada:
        # Salvar a imagem processada em um buffer
        buffer = io.BytesIO()
        imagem_processada.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Enviar a imagem processada
        await ctx.send(f"Aqui está sua imagem quadrificada:", file=discord.File(buffer, filename=f"quadrificado_{imagem_anexada.filename.split('.')[0]}.png"))
    else:
        await ctx.send("Houve um erro ao processar a imagem.")

# Iniciar o servidor web para manter o bot online
keep_alive()

# Iniciar o bot
if __name__ == "__main__":
    token = os.environ.get('discord_token')
    if not token:
        print("ERRO: Variável de ambiente discord_token não configurada!")
    else:
        bot.run(token)
