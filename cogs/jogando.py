import discord
from discord.ext import commands
import os
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class Jogando(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        self.temas_pasta = os.environ.get("temas_path", os.path.join(os.path.dirname(__file__), "temas"))
        self.jogos_ativos = {}  # Dicionário para rastrear jogos ativos por usuário e canal
        self.tema_mapeamento = self.carregar_tema_mapeamento()  # Carregar o mapeamento

    def carregar_tema_mapeamento(self):
        """
        Cria um dicionário que mapeia nomes de temas normalizados
        para os nomes reais das pastas de temas.
        """
        mapeamento = {}
        for pasta in os.listdir(self.temas_pasta):
            nome_normalizado = pasta.lower().replace(" ", "")
            mapeamento[nome_normalizado] = pasta  # Mapeia o nome normalizado para o nome real da pasta
            logging.debug(f"Tema mapeado: {nome_normalizado} -> {pasta}")
        return mapeamento

    @commands.command()
    async def jogando(self, ctx, *args):
        """Inicia ou finaliza o jogo de adivinhar palavras em um tema específico."""

        jogador_atual = ctx.author.id
        canal_atual = ctx.channel.id

        if "fim" in args:
            if (jogador_atual, canal_atual) in self.jogos_ativos:
                del self.jogos_ativos[(jogador_atual, canal_atual)]
                await ctx.send("Ajuda de imagens finalizada.")
            else:
                await ctx.send("Não há ajuda de jogo para você neste canal.")
            return

        tema = " ".join(args)
        tema = tema.strip()  # Remove espaços extras no início e no final
        tema_normalizado = tema.lower().replace(" ", "") # Nome normalizado para busca

        tema_pasta = None
        tema_nome_exibicao = None

        # Usar o mapeamento para encontrar o nome real da pasta
        if tema_normalizado in self.tema_mapeamento:
            tema_nome_exibicao = self.tema_mapeamento[tema_normalizado]  # Nome real da pasta
            tema_pasta = os.path.join(self.temas_pasta, tema_nome_exibicao)
            logging.debug(f"Tema encontrado no mapeamento: {tema_normalizado} -> {tema_nome_exibicao}")
        else:
            await ctx.send(f"Tema '{tema}' não encontrado.")
            return

        # Modifique esta linha para buscar o arquivo "lista_tema.txt"
        lista_palavras_path = os.path.join(tema_pasta, f"lista_{tema_normalizado}.txt")

        try:
            with open(lista_palavras_path, "r", encoding="utf-8") as f:
                palavras_tema = [linha.strip() for linha in f.readlines()]
        except FileNotFoundError:
            await ctx.send(
                f"Arquivo 'lista_{tema_normalizado}.txt' não encontrado na pasta do tema '{tema_nome_exibicao}'.")
            return
        except Exception as e:
            await ctx.send(
                f"Erro ao ler o arquivo 'lista_{tema_normalizado}.txt' para o tema '{tema_nome_exibicao}': {e}")
            return

        tema_atual = tema_nome_exibicao  # Usar o nome real da pasta

        # Armazenar as informações do jogo no dicionário
        self.jogos_ativos[(jogador_atual, canal_atual)] = {
            'tema': tema_atual,
            'palavras_tema': palavras_tema,
            'jogador': jogador_atual
        }

        await ctx.send(f"Você está jogando {tema_atual}.  Se precisar de uma imagem desse tema só falar.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Monitora as mensagens e verifica se contêm palavras do tema atual.
        """

        # Ignorar mensagens do próprio bot
        if message.author == self.bot.user:
            return

        jogador_atual = message.author.id
        canal_atual = message.channel.id

        # Verificar se há um jogo ativo para este usuário e canal
        if (jogador_atual, canal_atual) not in self.jogos_ativos:
            return

        jogo = self.jogos_ativos[(jogador_atual, canal_atual)]
        tema_atual = jogo['tema']  # Nome real da pasta!
        palavras_tema = jogo['palavras_tema']

        # Verificar se a mensagem contém alguma das palavras da lista para o tema atual
        mensagem_lower = message.content.lower()

        palavra_encontrada = None
        for palavra in palavras_tema:
            if mensagem_lower == palavra.lower():  # Verifica se a mensagem é *exatamente* a palavra
                palavra_encontrada = palavra
                break  # Encontrou uma palavra, pode sair do loop.

        if palavra_encontrada:
            # Obtém o nome base da imagem
            nome_base_imagem = f"{tema_atual} {palavra_encontrada}"  # tema_atual já é o nome correto da pasta
            caminho_imagem = None
            nome_imagem_completo = None

            # Procura a imagem com a extensão correta
            for ext in ['.png', '.jpg', '.jpeg', '.gif']:
                nome_imagem_teste = nome_base_imagem + ext
                caminho_teste = os.path.join(self.temas_pasta, tema_atual, nome_imagem_teste) # Usando tema_atual aqui!
                logging.debug(f"Testando caminho: {caminho_teste}")

                if os.path.exists(caminho_teste):
                    caminho_imagem = caminho_teste
                    nome_imagem_completo = nome_imagem_teste
                    logging.debug(f"Imagem encontrada em: {caminho_imagem}")
                    break
                else:
                    logging.debug(f"Imagem não encontrada em: {caminho_teste}")

            # Se a imagem foi encontrada, cria o embed e o botão
            if caminho_imagem:
                embed = discord.Embed(
                    title="Palavra Encontrada!",
                    description=f"Palavra encontrada em {tema_atual}.",
                    color=discord.Color.green()
                )
                embed.set_footer(text="Clique no botão abaixo para ver a imagem.")

                botao = discord.ui.Button(style=discord.ButtonStyle.primary, label="Mostrar Imagem")

                async def botao_callback(interaction: discord.Interaction):
                    # Garante que apenas o usuário que clicou no botão possa ver a mensagem
                    if interaction.user.id != jogador_atual:
                        await interaction.response.send_message("Você não pode usar este botão.", ephemeral=True)
                        return

                    try:
                        file = discord.File(caminho_imagem, filename="image" + os.path.splitext(nome_imagem_completo)[1])
                        embed_imagem = discord.Embed(title=f"Imagem: {tema_atual} - {palavra_encontrada}")
                        embed_imagem.set_image(url=f"attachment://image{os.path.splitext(nome_imagem_completo)[1]}")

                        # Cria o botão "Mostrar"
                        mostrar_button = discord.ui.Button(label="Mostrar", style=discord.ButtonStyle.success)

                        async def mostrar_callback(interaction2: discord.Interaction):
                            if interaction2.user.id != jogador_atual:
                                await interaction2.response.send_message("Você não pode usar este botão.", ephemeral=True)
                                return

                            try:
                                reenvia_file = discord.File(caminho_imagem, filename="image" + os.path.splitext(nome_imagem_completo)[1])
                                embed_reenviar = discord.Embed(title=f"Imagem: {tema_atual} - {palavra_encontrada}")
                                embed_reenviar.set_image(url=f"attachment://image{os.path.splitext(nome_imagem_completo)[1]}")
                                await interaction2.response.send_message(embed=embed_reenviar, file=reenvia_file, ephemeral=False)
                            except FileNotFoundError:
                                await interaction2.response.send_message(f"Imagem '{nome_base_imagem}' não encontrada.", ephemeral=True)
                            except Exception as e:
                                await interaction2.response.send_message(f"Ocorreu um erro ao enviar a imagem: {e}", ephemeral=True)

                        mostrar_button.callback = mostrar_callback

                        # Cria a View para o Embed ephemeral
                        view_ephemeral = discord.ui.View()
                        view_ephemeral.add_item(mostrar_button)

                        await interaction.response.send_message(embed=embed_imagem, file=file, view=view_ephemeral, ephemeral=True)

                    except FileNotFoundError:
                        await interaction.response.send_message(f"Erro ao enviar a imagem '{nome_base_imagem}'.", ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f"Ocorreu um erro ao enviar a imagem: {e}", ephemeral=True)

                botao.callback = botao_callback

                view = discord.ui.View()
                view.add_item(botao)
                await message.reply(embed=embed, view=view)

            # Se a imagem NÃO foi encontrada, envia uma mensagem diferente
            else:
                embed = discord.Embed(
                    title="Palavra Encontrada!",
                    description=f"Palavra encontrada em {tema_atual}.",
                    color=discord.Color.orange()  # Cor diferente para indicar falta de imagem
                )
                embed.add_field(name="Sem Imagem", value="Esta palavra não possui imagem para consulta.", inline=False)
                await message.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Jogando(bot))