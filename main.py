import random
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

prefixos = ["sailor ", "oi ", "Oi "]
permissoes = discord.Intents.all()
bot = commands.Bot(command_prefix=prefixos, intents=permissoes)


async def carregar_cogs():
    for arquivo in os.listdir('cogs'):  # Verifica todos os arquivos na pasta 'cogs'
        if arquivo.endswith('.py'):  # Carrega apenas arquivos .py
            try:
                # Tenta carregar a extensão
                bot.load_extension(f"cogs.{arquivo[:-3]}")  # Remove a extensão '.py' do nome do arquivo
                print(f"Cog {arquivo} carregado com sucesso!")
            except Exception as e:
                print(f"Erro ao carregar {arquivo}: {e}")


@bot.event
async def on_ready():
    canal = bot.get_channel(736438068206108742)
    await canal.send('Estou online e pronta para a ação!')
    await carregar_cogs()
    await bot.tree.sync()
    print("Estou pronta!")


@bot.command()
async def sincronizar(ctx: commands.Context):
    if ctx.author.id == 400318261306195988:
        servidor = discord.Object(id=982290881317072906)
        sincronizados = await bot.tree.sync(guild=servidor)
        await ctx.reply(f"{len(sincronizados)} comandos sincronizados.")
    else:
        await ctx.reply('Apenas o desenvolvedor pode usar esse comando.')


@bot.tree.command(description='Verifica o código hexadecimal de uma cor.')
@app_commands.choices(cores=[
    app_commands.Choice(name='Vermelho', value='BA2D08'),
    app_commands.Choice(name='Azul', value='22577A'),
    app_commands.Choice(name='Amarelo', value='FFC145')
])
async def cores(interact: discord.Interaction, cores: app_commands.Choice[str]):
    await interact.response.send_message(f"O código hexadecimal da cor {cores.name} é {cores.value}")


@bot.command()
async def enviar_embed(ctx: commands.Context):
    usuario = ctx.author
    meu_embed = discord.Embed(title='Isto é um Título!', description='Nada a descrever...')
    meu_embed.set_author(name=f'{usuario.name}', icon_url=f'{usuario.display_avatar}')
    meu_embed.color = usuario.color
    meu_embed.add_field(name='Moedas', value=10, inline=False)
    meu_embed.add_field(name='Filme Favorito', value='Speed Racer', inline=True)
    meu_embed.add_field(name='Rank', value='Prata', inline=True)
    thumb_arquivo = discord.File('imagens/tumblr_760486386aebadbbb3ab9786c11b6127_db4d47e5_500.jpg', 'thumb.jpg')
    meu_embed.set_thumbnail(url='attachment://thumb.jpg')
    imagem_arquivo = discord.File('imagens/blushing-seven-from-scissor-seven-ir2acdjg3ykks8mc.jpg', 'imagem.jpg')
    meu_embed.set_image(url='attachment://imagem.jpg')
    meu_embed.set_footer(text='Beyond')
    await ctx.reply(files=[imagem_arquivo, thumb_arquivo], embed=meu_embed)


@bot.command()
async def emoji(ctx: commands.Context):
    servidores = bot.guilds
    servidor_aleatorio = random.choice(servidores)
    emojis_servidor = servidor_aleatorio.emojis
    emoji_aleatorio = random.choice(emojis_servidor)

    async def resposta_verde(interact: discord.Interaction):
        servidor_aleatorio = random.choice(servidores)
        emojis_servidor = servidor_aleatorio.emojis
        emoji_aleatorio = random.choice(emojis_servidor)
        await interact.response.send_message(str(emoji_aleatorio), ephemeral=False)

    async def resposta_vermelho(interact: discord.Interaction):
        usuario_que_clicou = await bot.fetch_user(interact.user.id)
        copy_aleatorio = random.choice(poemas)
        await interact.response.send_message(copy_aleatorio, ephemeral=True)
        await interact.followup.send(
            f'<:polissa:748541705850060870><:bey_sempapo:867486162906382357><:bey_sus:1019710785880076390><:bey_gasm:867486162602950676> __**ALERTA!!**__ {usuario_que_clicou.mention} **CLICOU NO BOTÃO VERMELHO!** __**ALERTA!!**__ <:bey_gasm:867486162602950676><:bey_sus:1019710785880076390><:bey_sempapo:867486162906382357><:polissa:748541705850060870>')

    def carregar_copypasta(arquivo, encoding='utf-8'):
        with open(arquivo, 'r', encoding=encoding) as f:
            poemas = f.read().split('---')
            return [poema.strip() for poema in poemas if poema.strip()]

    poemas = carregar_copypasta('copy_pasta.txt')
    aparência = discord.ui.View()
    botao_verde = discord.ui.Button(emoji=emoji_aleatorio, label='Emoji Aleatório', style=discord.ButtonStyle.green)
    botao_verde.callback = resposta_verde
    botao_vermelho = discord.ui.Button(emoji='<:dafuq:1022911887509311519>', label='<botao configuração> NAO APERTAR',
                                       style=discord.ButtonStyle.red)
    botao_vermelho.callback = resposta_vermelho
    aparência.add_item(botao_verde)
    aparência.add_item(botao_vermelho)
    mensagem = await ctx.reply(view=aparência)
    contador = 0

    async def verificar_novas_mensagens(mensagem, contador):
        def check(message):
            return message.channel == ctx.channel
        while True:
            msg = await bot.wait_for("message", check=check)
            contador += 1
            if contador >= 50:
                contador = 0
                nova_mensagem = await ctx.reply(view=aparência)
                break
        await verificar_novas_mensagens(nova_mensagem, contador)

    await verificar_novas_mensagens(mensagem, contador)


@bot.command()
async def jogo(ctx: commands.Context):
    async def selecionar_opções(interact: discord.Interaction):
        escolha = interact.data['values'][0]
        jogos = {'1': 'Minecraft', '2': 'DDtank', '3': 'Stardew Valley'}
        jogo_escolhido = jogos[escolha]
        await interact.response.send_message(f'Você escolheu **{jogo_escolhido}**.')

    menuSeleção = discord.ui.Select(placeholder='Selecione uma opção')
    opções = [
        discord.SelectOption(label='Minecraft', value='1'),
        discord.SelectOption(label='DDtank', value='2'),
        discord.SelectOption(label='Stardew Valley', value='3')
    ]
    menuSeleção.options = opções
    menuSeleção.callback = selecionar_opções
    aparência = discord.ui.View()
    aparência.add_item(menuSeleção)
    await ctx.send(view=aparência)

@bot.event
async def on_message(msg: discord.Message):
    await bot.process_commands(msg)
    autor = msg.author
    if autor.bot:
        return
    # print(f'Mensagem {msg.content} enviada por: {autor}')


@bot.event
async def on_message(msg_online: discord.Message):
    await bot.process_commands(msg_online)
    autor = msg_online.author
    canal = 736438068206108742
    # print (f"Autor: {autor} | Canal: {canal} | Mensagem: {msg_online.content}")
    try:
        if msg_online.channel.id == canal and "estou online" in msg_online.content.lower() and autor.id == 1171547983842660420:
            await msg_online.add_reaction('<:bey_vamotime:912464901384060958>')
    except Exception as e:
        print(f'Erro {e}.')

@bot.event
async def on_guild_channel_create(canal: discord.abc.GuildChannel):
    await canal.send(f"FIRST! <a:bey_tururu:1217510268737945650> {canal.id}")

@bot.event
async def on_member_join(membro: discord.Member):
    canal = bot.get_channel(1227642510520619010)
    meu_embed = discord.Embed()
    meu_embed.title = f"Boas vindas {membro.name}!"
    meu_embed.description = f"# Aproveite sua estadia. (Servidor: {membro.guild.name} - ID: {membro.guild.id})"
    meu_embed.set_thumbnail(url=membro.avatar)
    meu_embed.color = membro.colour
    imagem_arquivo = discord.File('imagens/4903eee17b037ecd0224c550a73ebd1e.gif', 'boasvindas.gif')
    meu_embed.set_image(url='attachment://boasvindas.gif')
    await canal.send(file=imagem_arquivo, embed=meu_embed)

@bot.event
async def on_member_remove(membro: discord.Member):
    canal = bot.get_channel(798321996396101692)
    meu_embed = discord.Embed()
    meu_embed.title = f"{membro.display_name} saiu do servidor!"
    meu_embed.description = f"Que tristeza. (Servidor: {membro.guild.name} - ID: {membro.guild.id})"
    meu_embed.set_thumbnail(url=membro.avatar)
    meu_embed.color = membro.colour

    imagem_arquivo = discord.File('imagens/4903eee17b037ecd0224c550a73ebd1e.gif', 'boasvindas.gif')
    meu_embed.set_image(url='attachment://boasvindas.gif')
    await canal.send(file=imagem_arquivo, embed=meu_embed)

bot.run(TOKEN)