import random
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os

load_dotenv()

token = os.getenv("discord_token")

prefixos = ["sailor ", "oi ", "Oi "]
permissoes = discord.Intents.all()
bot = commands.Bot(command_prefix=prefixos, intents=permissoes)

# Lista para acompanhar quais cogs foram carregados
cogs_carregados = []

async def carregar_cogs():
    # Verificar se o diretório 'cogs' existe
    if not os.path.exists('cogs'):
        print("O diretório 'cogs' não existe. Verificando caminho absoluto...")
        # Obter o diretório atual do script
        dir_atual = os.path.dirname(os.path.abspath(__file__))
        cogs_dir = os.path.join(dir_atual, 'cogs')
        
        if os.path.exists(cogs_dir):
            print(f"Diretório 'cogs' encontrado em: {cogs_dir}")
        else:
            print(f"Diretório 'cogs' não encontrado em: {cogs_dir}")
            return
    
    # Listar todos os arquivos no diretório cogs
    try:
        arquivos = os.listdir('cogs')
        print(f"Arquivos encontrados no diretório 'cogs': {arquivos}")
        
        for arquivo in arquivos:
            if arquivo.endswith('.py'):
                try:
                    nome_cog = f"cogs.{arquivo[:-3]}"
                    await bot.load_extension(nome_cog)
                    cogs_carregados.append(nome_cog)
                    # print(f"Cog carregado com sucesso: {nome_cog}")
                except Exception as e:
                    print(f"Erro ao carregar o cog {arquivo}: {str(e)}")
    except Exception as e:
        print(f"Erro ao listar arquivos no diretório 'cogs': {str(e)}")


@bot.event
async def on_ready():
    print(f"Bot está online como {bot.user.name} ({bot.user.id})")
    
    # Tentar enviar mensagem para o canal
    try:
        canal = bot.get_channel(736438068206108742)
        if canal:
            await canal.send('Estou online e pronta para a ação!')
        else:
            print("Canal não encontrado. ID do canal: 736438068206108742")
    except Exception as e:
        print(f"Erro ao enviar mensagem: {str(e)}")
    
    # Carregar cogs
    await carregar_cogs()
    
    # Sincronizar comandos
    try:
        print("Tentando sincronizar comandos...")
        comandos = await bot.tree.sync()
        print(f"Comandos sincronizados: {len(comandos)}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {str(e)}")
    
    print("Inicialização completa!")


@bot.command()
async def sincronizar(ctx: commands.Context):
    if ctx.author.id == 400318261306195988:
        try:
            # Sincronização global
            sincronizados_global = await bot.tree.sync()
            
            # Sincronização para servidor específico
            servidor = discord.Object(id=982290881317072906)
            sincronizados_servidor = await bot.tree.sync(guild=servidor)
            
            await ctx.reply(f"{len(sincronizados_global)} comandos sincronizados globalmente.\n{len(sincronizados_servidor)} comandos sincronizados para o servidor.")
        except Exception as e:
            await ctx.reply(f"Erro ao sincronizar comandos: {str(e)}")
    else:
        await ctx.reply('Apenas o desenvolvedor pode usar esse comando.')


@bot.command()
async def listar_cogs(ctx: commands.Context):
    """Lista todos os cogs carregados."""
    if ctx.author.id == 400318261306195988:  # Verificar se é o desenvolvedor
        if cogs_carregados:
            await ctx.reply(f"Cogs carregados: {', '.join(cogs_carregados)}")
        else:
            await ctx.reply("Nenhum cog foi carregado.")
    else:
        await ctx.reply('Apenas o desenvolvedor pode usar esse comando.')


# Removi a duplicação da função on_message

@bot.event
async def on_message(msg: discord.Message):
    # Primeiro, processar comandos
    await bot.process_commands(msg)
    
    # Depois, verificar outras condições
    autor = msg.author
    if autor.bot:
        return
    
    # Verificar mensagem "estou online"
    canal_id = 736438068206108742
    try:
        if msg.channel.id == canal_id and "estou online" in msg.content.lower() and autor.id == 1171547983842660420:
            await msg.add_reaction('<:bey_vamotime:912464901384060958>')
    except Exception as e:
        print(f'Erro ao processar mensagem: {e}')


# Outras funções de evento permanecem as mesmas
@bot.event
async def on_guild_channel_create(canal: discord.abc.GuildChannel):
    try:
        await canal.send(f"FIRST! <a:bey_tururu:1217510268737945650> {canal.id}")
    except Exception as e:
        print(f'Erro ao enviar mensagem em canal novo: {e}')


@bot.event
async def on_member_join(membro: discord.Member):
    canal = bot.get_channel(1227642510520619010)
    if not canal:
        print(f"Canal de boas-vindas não encontrado (ID: 1227642510520619010)")
        return
    
    try:
        meu_embed = discord.Embed()
        meu_embed.title = f"Boas vindas {membro.name}!"
        meu_embed.description = f"# Aproveite sua estadia. (Servidor: {membro.guild.name} - ID: {membro.guild.id})"
        if membro.avatar:
            meu_embed.set_thumbnail(url=membro.avatar)
        meu_embed.color = membro.colour
        
        # Verificar se o arquivo de imagem existe
        imagem_path = 'imagens/4903eee17b037ecd0224c550a73ebd1e.gif'
        if os.path.exists(imagem_path):
            imagem_arquivo = discord.File(imagem_path, 'boasvindas.gif')
            meu_embed.set_image(url='attachment://boasvindas.gif')
            await canal.send(file=imagem_arquivo, embed=meu_embed)
        else:
            print(f"Arquivo de imagem não encontrado: {imagem_path}")
            await canal.send(embed=meu_embed)
    except Exception as e:
        print(f'Erro ao enviar mensagem de boas-vindas: {e}')


@bot.event
async def on_member_remove(membro: discord.Member):
    canal = bot.get_channel(798321996396101692)
    if not canal:
        print(f"Canal de saída não encontrado (ID: 798321996396101692)")
        return
    
    try:
        meu_embed = discord.Embed()
        meu_embed.title = f"{membro.display_name} saiu do servidor!"
        meu_embed.description = f"Que tristeza. (Servidor: {membro.guild.name} - ID: {membro.guild.id})"
        if membro.avatar:
            meu_embed.set_thumbnail(url=membro.avatar)
        meu_embed.color = membro.colour
        
        # Verificar se o arquivo de imagem existe
        imagem_path = 'imagens/4903eee17b037ecd0224c550a73ebd1e.gif'
        if os.path.exists(imagem_path):
            imagem_arquivo = discord.File(imagem_path, 'boasvindas.gif')
            meu_embed.set_image(url='attachment://boasvindas.gif')
            await canal.send(file=imagem_arquivo, embed=meu_embed)
        else:
            print(f"Arquivo de imagem não encontrado: {imagem_path}")
            await canal.send(embed=meu_embed)
    except Exception as e:
        print(f'Erro ao enviar mensagem de saída: {e}')


bot.run(token)