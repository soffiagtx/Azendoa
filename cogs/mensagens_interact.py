import discord
from discord import app_commands
from discord.ext import commands
import re

class MensagensInteract(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(description='Construa uma mensagem para enviar.')
    async def mensagem(self, interact:discord.Interaction):
        await interact.response.send_modal(Mensagem_Modal())

    @app_commands.command(description='Fala uma mensagem que o usuário digitou.')
    @app_commands.describe(frase='Digite uma frase')
    async def falar(self, interact:discord.Interaction, frase:str):
        canal = interact.channel
        await canal.send(frase)
        await interact.response.send_message(f"Mensagem enviada para <#{canal.id}>", ephemeral=True)

    @app_commands.command(description='Inicia uma partida de detetive.'
                          )
    async def detetive(self, interact:discord.Interaction):
        usuario_inicial = interact.user
        cargo_detetive = ['779957268929183759']

        embedo = discord.Embed(title='Detetive', description='Jogue Detetive com seus amigos.')
        embedo.set_author(name=f'{usuario_inicial.name}', icon_url=f'{usuario_inicial.display_avatar}')

        embedo.color = usuario_inicial.color

        embedo.add_field(name='Como jogar', value='Faça perguntas para descobrir quem está mentindo, mas cuidado para não revelar o local para o impostor!', inline=False)
        embedo.add_field(name='Quantidade de pessoas', value='3 a 10')

        thumb_detetive = discord.File('imagens/explorar.png', 'thumb.png')
        embedo.set_thumbnail(url='attachment://thumb.png')
        
        embedo.set_image(url='https://media1.tenor.com/m/N_bhbnT9xZYAAAAd/among-us-among-us-distraction-dance.gif')

        embedo.set_footer(text='Beyond')

        async def resposta_verde(interact:discord.Interaction):
            await interact.response.send_message("Você entrou no jogo!", ephemeral=True)

        async def resposta_azul(interact:discord.Interaction):
            if interact.user.id == usuario_inicial or interact.user.roles == cargo_detetive:
                await interact.response.send_message("Jogo Iniciando", ephemeral=True)
            else:
                await interact.response.send_message(f"Calma aí! Aguarde até {usuario_inicial.mention} iniciar o jogo.")

        async def resposta_cinza(interact:discord.Interaction):
            await interact.response.send_message(f"Regras do Detetive: ", ephemeral=True)

        aparência = discord.ui.View()
        botão_verde = discord.ui.Button(emoji='<a:star:1054840680402403458>', label='Entrar', style=discord.ButtonStyle.green)
        botão_verde.callback = resposta_verde
        botão_azul = discord.ui.Button(emoji='<:bey_sherlock:1023575351303082105>', label='Iniciar jogo', style=discord.ButtonStyle.blurple)
        botão_azul.callback = resposta_azul
        botão_cinza = discord.ui.Button(emoji='<:noface:996585044539879536>', label='Regras', style=discord.ButtonStyle.gray)
        botão_cinza.callback = resposta_cinza

        aparência.add_item(botão_verde)
        aparência.add_item(botão_azul)
        aparência.add_item(botão_cinza)
        await interact.response.send_message(files=[thumb_detetive], embed=embedo, view=aparência)

class Mensagem_Modal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title='Enviar Mensagem em um Canal')

    canal = discord.ui.TextInput(label='Canal (Opcional)', placeholder='Digite o ID do canal onde a mensagem será enviada', max_length=30, required=False)
    link_mensagem = discord.ui.TextInput(label='Link da Mensagem (Opcional)', placeholder='Digite o link da mensagem que será respondida', required=False)
    mensagem = discord.ui.TextInput(label='Digite a mensagem', style=discord.TextStyle.long)
    async def on_submit(self, interact:discord.Interaction):       
        id_canal = self.canal.value
        canal_destino = interact.guild.get_channel(int(id_canal)) if id_canal else interact.channel
        
        if not canal_destino.permissions_for(interact.guild.me).send_messages:
            await interact.response.send_message(f"Não é possível enviar mensagens em <#{canal_destino.id}>.", ephemeral=True)
            return
        
        try:
            if self.link_mensagem.value:
                match = re.search(r'/(\d+)$', self.link_mensagem.value)
                if match:
                    mensagem_id = int(match.group(1))
                    mensagem_link = await canal_destino.fetch_message(mensagem_id)
                    await mensagem_link.reply(self.mensagem.value)
                else:
                    raise ValueError("Link de mensagem inválido")               
            else:
                await canal_destino.send(self.mensagem.value)

            await interact.response.send_message(f"Mensagem enviada com sucesso a <#{canal_destino.id}>.", ephemeral=True)
        except discord.Forbidden:
            await interact.response.send_message(f"O bot não tem permissão para acessar o canal <#{canal_destino.id}>.", ephemeral=True)
        except discord.NotFound:
            await interact.response.send_message(f"Não foi possível encontrar a mensagem referenciada pelo link.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MensagensInteract(bot))