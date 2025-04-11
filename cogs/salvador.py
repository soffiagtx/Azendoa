import discord
from discord import app_commands
from discord.ext import commands, tasks
import random
import os
import json
import asyncio
from datetime import datetime, timedelta
import io

class Salvador(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        self.tema_canais = {}
        self.cooldowns = {}  # Cooldowns por palavra
        self.cooldown_geral = None  # Cooldown geral
        self.imagens_salvas = {}
        self.imagens_nao_encontradas = []
        self.owner_id = 400318261306195988
        self.canal_comandos_id = 1357094802956750978
        self.guild_alvo_id = 1313681515921801237
        self.guild_destino_id = 770057273447284796
        self.bot_alvo_id = 628120853154103316
        self.load_tema_canais()
        self.load_imagens_salvas()
        self.esperando_resposta = False
        self.atual_tema = None
        self.atual_palavra = None
        self.comando_atual_numero = 1
        self.cooldown_timestamps = {}
        self.bot.session = bot.http._HTTPClient__session
        self.proxima_execucao = None  # Nova variável para controlar quando o próximo comando será enviado

    def load_tema_canais(self):
        try:
            with open("tema_canais.json", "r", encoding='utf-8') as f:
                self.tema_canais = json.load(f)
        except FileNotFoundError:
            self.tema_canais = {}
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar tema_canais.json: {e}. Usando um dicionário vazio.")
            self.tema_canais = {}

    def save_tema_canais(self):
        with open("tema_canais.json", "w", encoding='utf-8') as f:
            json.dump(self.tema_canais, f, indent=4, ensure_ascii=False)

    def load_imagens_salvas(self):
        try:
            with open("imagens_salvas.json", "r", encoding='utf-8') as f:
                self.imagens_salvas = json.load(f)
        except FileNotFoundError:
            self.imagens_salvas = {}
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar imagens_salvas.json: {e}. Usando um dicionário vazio.")
            self.imagens_salvas = {}

    def save_imagens_salvas(self):
        with open("imagens_salvas.json", "w", encoding='utf-8') as f:
            json.dump(self.imagens_salvas, f, indent=4, ensure_ascii=False)

    def is_owner():
        async def predicate(ctx):
            return ctx.author.id == 400318261306195988
        return commands.check(predicate)

    def get_proxima_palavra(self, tema):
        tema_dir = os.path.join("cogs", "temas", tema)
        lista_arquivo = f"lista_{tema}.txt"
        caminho_arquivo = os.path.join(tema_dir, lista_arquivo)

        if not os.path.exists(caminho_arquivo):
            print(f"Arquivo de palavras para o tema '{tema}' não encontrado.")
            return None

        if tema not in self.imagens_salvas:
            self.imagens_salvas[tema] = {}

        try:
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                palavras = [linha.strip() for linha in f]
        except Exception as e:
            print(f"Erro ao ler o arquivo de palavras para o tema '{tema}': {e}")
            return None

        for palavra in palavras:
            if palavra not in self.imagens_salvas.get(tema, {}):
                return palavra

        return None

    @commands.command()
    @is_owner()
    async def salvar(self, ctx):
        guild_id = self.guild_destino_id
        canal_comandos_id = self.canal_comandos_id
        guild = self.bot.get_guild(guild_id)

        if guild is None:
            await ctx.send("Servidor alvo não encontrado.")
            return

        temas_dir = os.path.join("cogs", "temas")
        if not os.path.exists(temas_dir):
            await ctx.send("Pasta 'temas' não encontrada.")
            return

        temp_tema_canais = {}

        for canal in guild.text_channels:
            if canal.name.startswith("📂│"):
                try:
                    tema = canal.name.split("│", 1)[1].strip()
                    temp_tema_canais[tema.lower()] = canal.id
                    print(f"Canal para o tema '{tema}' encontrado: {canal.name} ({canal.id})")
                except IndexError:
                    print(f"Canal com nome inesperado: {canal.name}")

        self.tema_canais = temp_tema_canais
        self.save_tema_canais()
        print("Dados dos canais salvos em tema_canais.json")

        canal_comandos = self.bot.get_channel(canal_comandos_id)
        if canal_comandos:
            await canal_comandos.send("Canais salvos, iniciando busca por imagens.")
            await self.enviar_comando_inicial()
            self.enviar_proxima_palavra.start()  # Inicia a task aqui
        else:
            await ctx.send("Canal de comandos não encontrado.")

    async def enviar_comando_inicial(self):
        canal_comandos = self.bot.get_channel(self.canal_comandos_id)

        if not canal_comandos:
            print("Canal de comandos não encontrado.")
            return

        print("Iniciando enviar_comando_inicial...")
        try:
            temas = os.listdir(os.path.join("cogs", "temas"))
            print(f"Temas encontrados: {temas}")
            for tema in temas:
                tema_path = os.path.join("cogs", "temas", tema)
                print(f"Analisando tema: {tema_path}")
                if not os.path.isdir(tema_path):
                    print(f"'{tema_path}' não é um diretório. Ignorando.")
                    continue

                proxima_palavra = self.get_proxima_palavra(tema)
                if proxima_palavra:
                    comando = f".ver {tema} {proxima_palavra.lower()}"
                    mensagem = f"{self.comando_atual_numero} Use o comando `{comando}`"
                    await canal_comandos.send(mensagem)
                    self.atual_tema = tema
                    self.atual_palavra = proxima_palavra
                    self.esperando_resposta = True
                    print(f"Comando inicial enviado: {comando}")
                    return
                else:
                    print(f"Nenhuma palavra não salva encontrada para o tema '{tema}'.")
        except Exception as e:
            print(f"Erro ao enviar o comando inicial: {e}")

    @tasks.loop(seconds=5)  # Verifica a cada 5 segundos se é hora de enviar o próximo comando
    async def enviar_proxima_palavra(self):
        try:
            # Se estiver esperando resposta, não faz nada
            if self.esperando_resposta:
                print("Aguardando resposta do último comando.")
                return

            # Verifica se existe um tempo programado para a próxima execução
            if self.proxima_execucao is not None:
                # Se ainda não chegou o momento de executar, não faz nada
                if datetime.now() < self.proxima_execucao:
                    tempo_restante = (self.proxima_execucao - datetime.now()).total_seconds()
                    print(f"Aguardando cooldown: {tempo_restante:.2f} segundos restantes.")
                    return
                else:
                    # Limpa o temporizador pois já chegou a hora de executar
                    self.proxima_execucao = None

            # Cooldown geral
            if self.cooldown_geral and datetime.now() < self.cooldown_geral:
                tempo_restante = (self.cooldown_geral - datetime.now()).total_seconds()
                print(f"Cooldown geral ativo. Aguardando {tempo_restante:.2f} segundos.")
                return

            if self.atual_tema is None:
                print("Nenhum tema atual definido. Buscando próximo tema...")
                # Busca um tema que tenha palavras não salvas
                for tema in os.listdir(os.path.join("cogs", "temas")):
                    if not os.path.isdir(os.path.join("cogs", "temas", tema)):
                        continue
                    proxima_palavra = self.get_proxima_palavra(tema)
                    if proxima_palavra:
                        self.atual_tema = tema
                        self.atual_palavra = proxima_palavra
                        break
                if not self.atual_tema:
                    print("Nenhum tema com palavras não salvas encontrado.")
                    return

            proxima_palavra = self.get_proxima_palavra(self.atual_tema)
            if not proxima_palavra:
                print(f"Todas as palavras do tema '{self.atual_tema}' já foram salvas. Buscando próximo tema...")
                self.atual_tema = None  # Limpa o tema para que o próximo seja buscado
                self.atual_palavra = None
                return

            # Cooldown individual da palavra
            if self.em_cooldown(self.bot_alvo_id, proxima_palavra):
                print(f"A palavra '{proxima_palavra}' está em cooldown. Pulando...")
                return

            comando = f".ver {self.atual_tema} {proxima_palavra.lower()}"
            mensagem = f"{self.comando_atual_numero} Use o comando `{comando}`"
            canal_comandos = self.bot.get_channel(self.canal_comandos_id)

            if canal_comandos:
                await canal_comandos.send(mensagem)
                print(f"Comando enviado: {comando}")
            else:
                print("Canal de comandos não encontrado.")
                return

            self.atual_palavra = proxima_palavra
            self.esperando_resposta = True

        except Exception as e:
            print(f"Erro em enviar_proxima_palavra: {e}")

    def proximo_comando(self):
        self.comando_atual_numero += 1
        if self.comando_atual_numero > 3:
            self.comando_atual_numero = 1

    # Define quando o próximo comando deve ser enviado
    def agendar_proximo_comando(self, segundos):
        self.proxima_execucao = datetime.now() + timedelta(seconds=segundos)
        print(f"Próximo comando agendado para {self.proxima_execucao.strftime('%H:%M:%S')} (em {segundos} segundos)")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot_alvo_id and message.channel.id == self.canal_comandos_id and message.guild.id == self.guild_alvo_id:
            if self.esperando_resposta:
                if message.embeds:
                    embed = message.embeds[0]
                    cooldown_aleatorio = random.randint(21, 31)  # Define o cooldown aleatório entre 20 e 30 segundos

                    if embed.color.value == 16627968 and ":Relogio:" in embed.description:  # Verifica cooldown
                        tempo_restante = self.extrair_tempo_restante(embed.description)
                        self.definir_cooldown(message.author.id, self.atual_palavra, tempo_restante)
                        print(f"Cooldown detectado para '{self.atual_palavra}'. Tentando novamente em {tempo_restante} segundos.")
                        self.esperando_resposta = False
                        self.proximo_comando()
                        print(f"Aguardando {cooldown_aleatorio} segundos antes de enviar o próximo comando...")
                        self.agendar_proximo_comando(cooldown_aleatorio)  # Agenda o próximo comando

                    elif embed.color.value == 16627968 and "<:Erro:" in embed.description:  # Palavra não encontrada
                        print(f"Palavra '{self.atual_palavra}' não encontrada no tema '{self.atual_tema}'.")
                        self.salvar_palavra_nao_encontrada(self.atual_tema, self.atual_palavra)
                        self.esperando_resposta = False
                        self.proximo_comando()
                        print(f"Aguardando {cooldown_aleatorio} segundos antes de enviar o próximo comando...")
                        self.agendar_proximo_comando(cooldown_aleatorio)  # Agenda o próximo comando

                    else:  # Imagem encontrada
                        if embed.image:
                            imagem_url = embed.image.url
                            tema_sem_espaco = self.atual_tema.replace(" ", "")
                            canal_tema_id = self.tema_canais.get(tema_sem_espaco.lower())

                            if canal_tema_id:
                                canal_tema = self.bot.get_channel(canal_tema_id)
                                if canal_tema:
                                    try:
                                        async with self.bot.session.get(imagem_url) as resp:
                                            if resp.status == 200:
                                                image_data = await resp.read()
                                                mensagem_enviada = await canal_tema.send(f"{self.atual_palavra.lower()}", file=discord.File(fp=io.BytesIO(image_data), filename=f"{self.atual_palavra.lower()}.png"))
                                                print(f"Imagem para '{self.atual_palavra}' enviada para o canal '{canal_tema.name}'.")

                                                # Salva a URL da imagem
                                                if mensagem_enviada.attachments:
                                                    url_imagem_enviada = mensagem_enviada.attachments[0].url
                                                else:
                                                    url_imagem_enviada = None

                                                # Marca a palavra como salva
                                                if self.atual_tema not in self.imagens_salvas:
                                                    self.imagens_salvas[self.atual_tema] = {}

                                                self.imagens_salvas[self.atual_tema][self.atual_palavra] = url_imagem_enviada
                                                self.save_imagens_salvas()
                                                self.esperando_resposta = False
                                                self.proximo_comando()
                                                print(f"Aguardando {cooldown_aleatorio} segundos antes de enviar o próximo comando...")
                                                self.agendar_proximo_comando(cooldown_aleatorio)  # Agenda o próximo comando

                                            else:
                                                print(f"Erro ao baixar a imagem de {imagem_url}. Status: {resp.status}")
                                                self.esperando_resposta = False
                                                self.proximo_comando()
                                                print(f"Aguardando {cooldown_aleatorio} segundos antes de enviar o próximo comando...")
                                                self.agendar_proximo_comando(cooldown_aleatorio)  # Agenda o próximo comando

                                    except Exception as e:
                                        print(f"Erro ao processar a imagem: {e}")
                                        self.esperando_resposta = False
                                        self.proximo_comando()
                                        print(f"Aguardando {cooldown_aleatorio} segundos antes de enviar o próximo comando...")
                                        self.agendar_proximo_comando(cooldown_aleatorio)  # Agenda o próximo comando

                                else:
                                    print(f"Canal com ID {canal_tema_id} não encontrado.")
                                    self.esperando_resposta = False
                                    self.proximo_comando()
                                    print(f"Aguardando {cooldown_aleatorio} segundos antes de enviar o próximo comando...")
                                    self.agendar_proximo_comando(cooldown_aleatorio)  # Agenda o próximo comando
                            else:
                                print(f"Canal para o tema '{self.atual_tema}' não encontrado.")
                                self.esperando_resposta = False
                                self.proximo_comando()
                                print(f"Aguardando {cooldown_aleatorio} segundos antes de enviar o próximo comando...")
                                self.agendar_proximo_comando(cooldown_aleatorio)  # Agenda o próximo comando

    def em_cooldown(self, bot_id, palavra):
        if bot_id in self.cooldowns and palavra in self.cooldowns[bot_id]:
            return self.cooldowns[bot_id][palavra] > datetime.now()
        return False

    def definir_cooldown(self, bot_id, palavra, segundos):
        if bot_id not in self.cooldowns:
            self.cooldowns[bot_id] = {}
        self.cooldowns[bot_id][palavra] = datetime.now() + timedelta(seconds=segundos)
        # Define um cooldown geral após cada comando
        self.cooldown_geral = datetime.now() + timedelta(seconds=segundos)

    def remover_cooldown(self, bot_id, palavra):
        if bot_id in self.cooldowns and palavra in self.cooldowns[bot_id]:
            del self.cooldowns[bot_id][palavra]

    def extrair_tempo_restante(self, descricao):
        try:
            timestamp_inicio = descricao.find("<t:") + 3
            timestamp_fim = descricao.find(":R>")
            timestamp = int(descricao[timestamp_inicio:timestamp_fim])
            tempo_restante = timestamp - int(datetime.now().timestamp())
            return max(tempo_restante, 0)
        except Exception as e:
            print(f"Erro ao extrair o tempo restante: {e}")
            return 60

    def salvar_palavra_nao_encontrada(self, tema, palavra):
        nome_arquivo = "imagens_nao_encontradas.txt"
        with open(nome_arquivo, "a", encoding='utf-8') as arquivo:
            arquivo.write(f"Tema: {tema}, Palavra: {palavra}\n")

    @enviar_proxima_palavra.before_loop
    async def before_enviar_proxima_palavra(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Salvador(bot))