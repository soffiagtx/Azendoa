import discord
from discord.ext import commands
import random
import os
import time

class Emoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.servidor_escolhido = None
        super().__init__()

    @commands.command()
    async def emojis(self, ctx: commands.Context):
        usuario_inicial = ctx.author
        embedo = discord.Embed(title='<a:star:1054840680402403458> Emojis',
                              description='Navegue por emojis entre vários servidores.')

        embedo.color = usuario_inicial.color
        embedo.set_footer(icon_url='https://media.discordapp.net/attachments/990286786066534500/1218365665291800667/Beyond.png?ex=66076672&is=65f4f172&hm=4b4b773e6d60885598a56288074dacdf6c6d52300b8de2963484e21887eecacd&=&format=webp&quality=lossless&width=115&height=108',
                        text='Beyond')

        global servidor_escolhido
        servidores = self.bot.guilds
        servidores_com_emojis = []
        for servidor in servidores:
            if len(servidor.emojis) > 0:
                servidores_com_emojis.append(servidor)
        if len(servidores_com_emojis) == 0:
            await ctx.send("Nenhum servidor com emojis encontrado. 🥺")
            return

        servidor_aleatorio = random.choice(servidores_com_emojis)
        emojis_servidor = servidor_aleatorio.emojis
        emoji_aleatorio = random.choice(emojis_servidor)

        async def resposta_azul(interact: discord.Interaction):
            global servidor_escolhido
            if servidor_escolhido is not None:
                emojis_primeira_mensagem = servidor_escolhido.emojis[:30]
                emojis_str = ' '.join(str(emoji) for emoji in emojis_primeira_mensagem)
                await interact.response.send_message(emojis_str, ephemeral=False)

                for contador in range(30, len(servidor_escolhido.emojis), 30):
                    emojis = servidor_escolhido.emojis[contador:contador + 30]
                    emojis_str = ' '.join(str(emoji) for emoji in emojis)
                    await interact.followup.send(emojis_str, ephemeral=False)
            else:
                await interact.response.send_message("Por favor, selecionar um servidor primeiro.", ephemeral=True)

        async def resposta_cinza(interact: discord.Interaction):
            await interact.response.send_modal(IdServidorModal())

        async def servidores_seleção(interact: discord.Interaction):
            global servidor_escolhido
            servidor_escolhido_valor = int(interact.data['values'][0]) - 1
            servidores = self.bot.guilds
            servidor_escolhido = servidores[servidor_escolhido_valor]

            emojis_estáticos = sum(1 for emoji in servidor_escolhido.emojis if not emoji.animated)
            emojis_animados = sum(1 for emoji in servidor_escolhido.emojis if emoji.animated)
            total_emojis = len(servidor_escolhido.emojis)

            campos = [
                ("Servidor escolhido: ", servidor_escolhido, False),
                ("Emojis estáticos: ", emojis_estáticos, True),
                ("Emojis animados: ", emojis_animados, True),
                ("Emojis totais: ", total_emojis, True)
            ]

            embedo.clear_fields()

            for nome, valor, inline in campos:
                embedo.add_field(name=nome, value=valor, inline=inline)

            aparência.add_item(botão_verde)
            aparência.add_item(botão_azul)
            if interact.user.id in lista_ids_finnstrela:
                aparência.remove_item(botão_cinza)
                aparência.add_item(botão_cinza)
            await interact.response.edit_message(embed=embedo, view=aparência)

        async def enviar_emojis(interact: discord.Interaction):
            global servidor_escolhido

            if servidor_escolhido is not None:
                embedo = discord.Embed(title=f'{random.choice(servidor_escolhido.emojis)} Emojis de {servidor_escolhido}')
                embedo.set_author(name=f'{interact.user.name}', icon_url=f'{interact.user.display_avatar}')
                embedo.color = interact.user.color

                emojis_primeira_mensagem = servidor_escolhido.emojis[:12]
                emojis_str = ' '.join(str(emoji) for emoji in emojis_primeira_mensagem)
                embedo.add_field(name='', value=f'{emojis_str}', inline=False)

                for i in range(12, len(servidor_escolhido.emojis), 12):
                    emojis = servidor_escolhido.emojis[i:i + 12]
                    emojis_str = ' '.join(str(emoji) for emoji in emojis)
                    embedo.add_field(name='', value=f'{emojis_str}', inline=False)
                await interact.response.send_message(embed=embedo)
            else:
                await interact.response.send_message("Por favor, selecione um servidor primeiro.", ephemeral=True)

        menuSeleção = discord.ui.Select(placeholder='Selecione um servidor')
        opções = []

        contador = 0
        for servidor in self.bot.guilds:
            if servidor.emojis:
                emoji = random.choice(servidor.emojis)
                opções.append(discord.SelectOption(emoji=emoji, label=f'{servidor.name}', value=str(contador + 1)))
            contador += 1

        menuSeleção.options = opções
        menuSeleção.callback = servidores_seleção

        aparência = discord.ui.View()
        botão_verde = discord.ui.Button(emoji='<a:star_tovendo:893629235657330778> ', label='Ver Emojis', style=discord.ButtonStyle.green)
        botão_verde.callback = enviar_emojis
        botão_azul = discord.ui.Button(emoji=emoji_aleatorio, label='Enviar emojis', style=discord.ButtonStyle.blurple)
        botão_azul.callback = resposta_azul
        aparência.add_item(menuSeleção)

        lista_ids_finnstrela = [548819214606139403, 283654977401126912, 400318261306195988]
        if ctx.author.id in lista_ids_finnstrela:
            botão_cinza = discord.ui.Button(emoji='<a:star_diboinha:786634182142984233>', style=discord.ButtonStyle.gray)
            botão_cinza.callback = resposta_cinza
            aparência.add_item(botão_cinza)

        await ctx.send(embed=embedo, view=aparência)

class IdServidorModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title='Servidor de Emojis')

    id_servidor = discord.ui.TextInput(label='ID do Servidor', placeholder='Digite o ID do servidor para pegar os emojis', required=True)
    canal = discord.ui.TextInput(label='Canal para enviar as imagens (Opcional)', placeholder='Digite o ID de um canal para enviar as imagens pra lá', style=discord.TextStyle.long, required=False)

    async def on_submit(self, interact: discord.Interaction):
        id_servidor_digitado = self.id_servidor.value
        canal_imagens_digitado = self.canal.value
        canal_destino_id = 1227642510520619010
        canal_destino_imagens = interact.client.get_channel(int(canal_imagens_digitado)) if canal_imagens_digitado else interact.channel
        canal_destino = interact.client.get_channel(canal_destino_id)
        print(f"Canal destino das imagens {canal_destino_imagens}")
        print(f"CAnal destino da mensagem: {canal_destino}")
        await interact.response.send_message(f"Iniciando busca de emojis... ||{canal_destino.mention}||", ephemeral=False)
        await canal_destino.send(f"pipoquinhas {id_servidor_digitado}")

        resposta_usuário = await interact.client.wait_for('message', check=lambda message:message.author.id == 497854782434705408 and message.content.startswith("Emojis baixados do servidor "))
        if resposta_usuário is None:
            await interact.followup.send("Tempo limite para resposta excedido.", ephemeral=True)
            return

        nome_servidor = resposta_usuário.content
        if nome_servidor.startswith("Emojis baixados do servidor"):
            nome_servidor = nome_servidor[len("Emojis baixados do servidor "):]

        await interact.followup.send(f"Enviando emojis do servidor {nome_servidor} para {canal_destino_imagens.mention}", ephemeral=False)
        diretório_emojis = "C:\\Users\\user\\Desktop\\Programação\\Projetos Pessoais\\Discord\\bot se\\emojis\\servidor_alvo"
        arquivos_emojis = [arquivo for arquivo in os.listdir(diretório_emojis) if arquivo.endswith((".png", ".gif", ".jpg", ".jpeg"))]

        async def resposta_sim(interact: discord.Interaction):
          await self.criar_emojis_servidor(interact, arquivos_emojis, nome_servidor)

        async def resposta_não(interact: discord.Interaction):
            await interact.response.send_message('Ok. As imagens não serão transformadas em emojis.', ephemeral=True)

        aparência = discord.ui.View()
        botão_sim = discord.ui.Button(emoji='<:bey_yee:1005197024263684187>', label='si', style=discord.ButtonStyle.green)
        botão_sim.callback = resposta_sim
        botão_não = discord.ui.Button(emoji='<:bey_surrender:1021594598176460800>', label='nau', style=discord.ButtonStyle.red)
        botão_não.callback = resposta_não
        aparência.add_item(botão_sim)
        aparência.add_item(botão_não)
        
        
        for i in range(0, len(arquivos_emojis), 9):
            arquivos_lote = arquivos_emojis[i:i + 9]
            print("Enviando lote de imagens:", arquivos_lote)
            await canal_destino_imagens.send(files=[discord.File(os.path.join(diretório_emojis, arquivo)) for arquivo in arquivos_lote])
        print(f"Imagens de {nome_servidor} enviadas.")
        await interact.followup.send(f"Imagens dos emojis enviadas com sucesso.\nDeseja transformar as imagens de {nome_servidor} em emojis?", ephemeral=False, view=aparência)

    async def criar_emojis_servidor(self, interact: discord.Interaction, arquivos_emojis, nome_servidor):
        guild = interact.guild
        if not guild:
            await interact.response.send_message("Este comando só pode ser usado em um servidor.", ephemeral=True)
            return

        if not interact.user.guild_permissions.manage_emojis_and_stickers:
            await interact.response.send_message("Você não tem permissão para adicionar emojis neste servidor.", ephemeral=True)
            return

        if not guild.me.guild_permissions.manage_emojis_and_stickers:
            await interact.response.send_message("Eu não tenho permissão para adicionar emojis neste servidor.", ephemeral=True)
            return
        
        await interact.response.send_message('Iniciando a criação de emojis, isso pode demorar um pouco...', ephemeral=True)
        diretório_emojis = "C:\\Users\\user\\Desktop\\Programação\\Projetos Pessoais\\Discord\\bot se\\emojis\\servidor_alvo"
        
        emojis_adicionados = 0
        falhas = []
        
        for arquivo in arquivos_emojis:
          
            try:
              with open(os.path.join(diretório_emojis, arquivo), 'rb') as f:
                  emoji_image = f.read()
              
              emoji_name = os.path.splitext(arquivo)[0]
              emoji = await guild.create_custom_emoji(name=emoji_name, image=emoji_image)
              emojis_adicionados += 1
            except discord.errors.HTTPException as e:
                falhas.append(f'Falha ao adicionar {arquivo}: {e}')
                print(f"Erro ao criar emoji: {e}")
            except Exception as e:
                falhas.append(f'Erro inesperado ao criar {arquivo}: {e}')
                print(f"Erro inesperado: {e}")
            time.sleep(2)


        mensagem_final = f'Emojis adicionados: {emojis_adicionados}/{len(arquivos_emojis)}'
        if falhas:
            mensagem_final += '\n\nFalhas:\n' + '\n'.join(falhas)
        await interact.followup.send(mensagem_final, ephemeral=False)


async def setup(bot):
    await bot.add_cog(Emoji(bot))