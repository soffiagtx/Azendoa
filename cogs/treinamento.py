import discord
from discord import app_commands
from discord.ext import commands
from discord import ui
from typing import Optional
import re
import os
import requests
from io import BytesIO
from PIL import Image, ImageOps
import torch
import torchvision.transforms as transforms
from torch.nn.functional import cosine_similarity
import asyncio
import json
import unicodedata
import traceback
from datetime import datetime, timedelta

class Treinamento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        self.BASE_DIR = r"C:\Users\user\Desktop\Programação\Projetos Pessoais\Discord\bot az\temas"
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5])
        ])
        self.processing = set()  # Para rastrear usuários no modo de treinamento
        self.modified_names_file = os.path.join(self.BASE_DIR, "modified_names.json")
        self.modified_names = self.load_modified_names()
        self.training_configs = {}  # Dicionário para armazenar configurações por usuário
        self.GAME_BOT_ID = 628120853154103316  # ID do bot do jogo
        self.processed_messages = set()  # Para rastrear as mensagens já processadas

        # IDs específicos para o requerimento adicional
        self.TARGET_GUILD_ID = 623204625251827724
        self.OUTPUT_GUILD_ID = 771536853131984906
        self.OUTPUT_CHANNEL_ID = 800203231484837928


    def load_modified_names(self):
        if os.path.exists(self.modified_names_file):
            with open(self.modified_names_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    normalized_data = {self.normalize_text(key): self.normalize_text(value) for key, value in data.items()}
                    return normalized_data
                except json.JSONDecodeError:
                    print("Erro ao decodificar o arquivo JSON, criando um novo dicionário.")
                    return {}
        return {}

    def normalize_text(self, text):
        return unicodedata.normalize('NFC', text)

    def safe_filename(self, filename):
        invalid_chars = r'[:/\\<>|"\'?*#]'
        return re.sub(invalid_chars, '_', filename)

    def load_image(self, image_path):
        try:
            image = Image.open(image_path).convert('RGB')
            return self.transform(image).unsqueeze(0)
        except Exception as e:
            print(f"Erro ao carregar imagem {image_path}: {e}")
            return None

    def find_case_insensitive_path(self, base_path, target_name):
        for item in os.listdir(base_path):
            if item.lower() == target_name.lower():
                return os.path.join(base_path, item)
        return None

    def find_query_image(self, theme_images_dir, query_image_name):
        valid_extensions = ('.png', '.jpg', '.jpeg')
        for ext in valid_extensions:
            full_name = query_image_name + ext
            query_image_path = self.find_case_insensitive_path(theme_images_dir, full_name)
            if query_image_path:
                return query_image_path
        return None

    def compare_images(self, theme_images_dir, query_image_path):
        query_image = self.load_image(query_image_path)
        if query_image is None:
            print("Imagem de consulta não pôde ser carregada para comparação.")
            return []
        query_image = query_image.flatten(start_dim=1)

        valid_extensions = ('.png', '.jpg', '.jpeg')
        theme_images = [os.path.join(theme_images_dir, img) for img in os.listdir(theme_images_dir) if img.lower().endswith(valid_extensions)]

        similarities = []

        for img_path in theme_images:
            if os.path.basename(img_path) == os.path.basename(query_image_path):
                continue

            theme_image = self.load_image(img_path)
            if theme_image is None:
                print(f"Imagem do tema {img_path} não pôde ser carregada.")
                continue
            theme_image = theme_image.flatten(start_dim=1)

            similarity = cosine_similarity(query_image, theme_image, dim=1)
            similarities.append((similarity.item(), img_path))

        similarities.sort(reverse=True, key=lambda x: x[0])
        return similarities

    def add_border(self, image_path, theme):
        try:
            img = Image.open(image_path).convert("RGBA")
            largura, altura = img.size

            if largura != altura:
                tamanho_maximo = max(largura, altura)
                delta_largura = tamanho_maximo - largura
                delta_altura = tamanho_maximo - altura
                borda_esquerda = delta_largura // 2
                borda_direita = delta_largura - borda_esquerda
                borda_topo = delta_altura // 2
                borda_baixo = delta_altura - borda_topo
                if theme.startswith("Vet"):
                    cor_borda = (255, 255, 255, 255)  # Branco com alfa
                else:
                    cor_borda = (0, 0, 0, 0)  # Transparente

                img = ImageOps.expand(img, border=(borda_esquerda, borda_topo, borda_direita, borda_baixo), fill=cor_borda)
            return img
        except Exception as e:
            print(f"Erro ao adicionar borda: {e}")
            return None

    class TrainingConfigModal(ui.Modal, title='Configuração de Treinamento'):
        channel_link = ui.TextInput(label='Link do Canal', placeholder='https://discord.com/channels/...', required=True)
        theme = ui.TextInput(label='Tema', placeholder='Digite o nome do tema', required=True)

        def __init__(self, cog_instance):  # Aceita uma referência para a instância do cog
            super().__init__()
            self.cog = cog_instance  # Armazena a referência

        async def on_submit(self, interaction: discord.Interaction):
            channel_link = self.channel_link.value
            print(f"Link do canal recebido: {channel_link}")  # Log do link recebido

            # Validação básica para verificar se o link contém 'discord.com/channels/'
            if 'discord.com/channels/' not in channel_link:
                await interaction.response.send_message("Formato de link de canal inválido. Deve conter 'discord.com/channels/'.", ephemeral=True)
                return

            try:
                # Extrai guild_id e channel_id usando regex
                match = re.search(r'/channels/(\d+)/(\d+)', channel_link)
                if not match:
                    await interaction.response.send_message("Formato de link de canal inválido. Não foi possível extrair Guild ID e Channel ID.", ephemeral=True)
                    return

                guild_id = int(match.group(1))
                channel_id = int(match.group(2))

                print(f"Guild ID extraído: {guild_id}, Channel ID extraído: {channel_id}")  # Log dos IDs extraídos

            except ValueError as e:
                print(f"Erro ao converter IDs para inteiro: {e}")  # Log de erros na conversão
                await interaction.response.send_message("Formato de link de canal inválido. Guild ID ou Channel ID não são números inteiros.", ephemeral=True)
                return
            except Exception as e:
                print(f"Erro inesperado ao processar o link: {e}")
                await interaction.response.send_message("Ocorreu um erro inesperado ao processar o link.", ephemeral=True)
                return

             # Verificar se o tema existe
            theme_name = self.theme.value
            theme_dir = os.path.join(self.cog.BASE_DIR, theme_name)
            if not os.path.exists(theme_dir):
                await interaction.response.send_message(f"O tema '{theme_name}' não foi encontrado. Por favor, insira um tema válido.", ephemeral=True)
                return

            # Armazena os dados na classe Treinamento, usando o ID do usuário como chave
            self.cog.training_configs[interaction.user.id] = { # Usa a referência self.cog
                'guild_id': guild_id,
                'channel_id': channel_id,
                'theme_name': theme_name
            }

            await interaction.response.defer(ephemeral=True)  # Reconhece e adia
             # Envia mensagem para canal específico se a guild for a target
            if guild_id == self.cog.TARGET_GUILD_ID:
                 # Envia mensagem para o canal de coach e inicia o monitoramento especial
                await self.cog.send_coach_message(interaction, channel_id)
                await interaction.followup.send(
                    "Servidor oficial encontrado, um momento.", ephemeral=True
                )
                return

            # Se não for o servidor oficial, processar normalmente
            await self.cog.process_training_setup(interaction, interaction.user.id, guild_id, channel_id, theme_name)


        async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
            await interaction.response.send_message('Oops! Algo deu errado.', ephemeral=True)
            # Garante que sabemos qual é o erro
            traceback.print_exception(type(error), error, error, error.__traceback__)


    async def send_coach_message(self, interaction, channel_id):
        """Envia mensagem para o canal de coach especificado e inicia o monitoramento."""
        target_guild = self.bot.get_guild(self.OUTPUT_GUILD_ID)
        if not target_guild:
            print(f"Erro: Servidor com ID {self.OUTPUT_GUILD_ID} não encontrado.")
            return

        target_channel = target_guild.get_channel(self.OUTPUT_CHANNEL_ID)
        if not target_channel:
            print(f"Erro: Canal com ID {self.OUTPUT_CHANNEL_ID} não encontrado.")
            return
        
        try:
            # Envia mensagem de coach e armazena a mensagem para esperar a resposta
            coach_message = await target_channel.send(f"coach {channel_id}")
            
            # Inicia o monitoramento de mensagem para capturar a imagem
            await self.coach_image_monitor(interaction, channel_id, coach_message, target_channel)
            
        except Exception as e:
             print(f"Erro ao enviar mensagem para o canal de coach: {e}")

    async def coach_image_monitor(self, interaction, channel_id, coach_message, target_channel):
         """Monitora o canal de coach para uma imagem em resposta à mensagem 'coach <id>'."""
         user_id = interaction.user.id # Pega o id do usuario

         while user_id in self.processing: # Mantém o loop enquanto o usuário estiver no modo de treinamento

            def check(message):
                return message.channel == target_channel and message.reference and message.reference.message_id == coach_message.id and len(message.attachments) > 0
            
            try:
                # Espera por uma mensagem com imagem em resposta à mensagem do coach
                message = await self.bot.wait_for('message', check=check, timeout=120) # 2 min de timeout
                
                # Processa a imagem anexada
                attachment = message.attachments[0]
                image_bytes = await attachment.read()
                image = Image.open(BytesIO(image_bytes))
                
                # Configura o caminho para a imagem
                
                theme_name = self.training_configs[user_id]['theme_name']
                theme_dir = os.path.join(self.BASE_DIR, theme_name)
                theme_images_dir = os.path.join(theme_dir, f"imagens_{theme_name}_com_borda")
                
                # Salva a imagem na pasta de treinamento
                file_name = f"{user_id}_consulta"
                training_image_path = os.path.join(theme_images_dir, f"{file_name}.png")
                image.save(training_image_path)
                
                # Adiciona borda à imagem
                bordered_image = self.add_border(training_image_path, theme_name)
                if bordered_image:
                    bordered_image.save(training_image_path)  # Salva a imagem com borda

                # Compara a imagem com as outras na pasta com borda
                results = self.compare_images(theme_images_dir, training_image_path)
                print("Imagem de jogo recebida") #print de imagem recebida

                if results:
                    score, img_path = results[0]  # Maior similaridade
                    current_image_name = os.path.splitext(os.path.basename(img_path))[0] # Salva o nome da imagem atual
                    img_name = current_image_name
                    similarity_percentage = score * 100 # Converte a similaridade em porcentagem
                    
                    # Encontra a imagem original (sem borda)
                    original_image_path = os.path.join(theme_dir, f"{img_name}.png")  # Adapte a extensão se necessário
                    if not os.path.exists(original_image_path):
                        original_image_path = os.path.join(theme_dir, f"{img_name}.jpg")
                    if not os.path.exists(original_image_path):
                        original_image_path = os.path.join(theme_dir, f"{img_name}.jpeg")

                    if os.path.exists(original_image_path):
                        file = discord.File(original_image_path, filename="image.png")
                        embed = discord.Embed(
                            title="Resultado da Identificação",
                            description=f"Similaridade: {similarity_percentage:.2f}%\n\nNão é a resposta? clique no botão abaixo para ver outras possíveis respostas", # Mostra o nome da imagem e a porcentagem
                        )
                        embed.set_thumbnail(url=f"attachment://image.png") # Adiciona a imagem como thumbnail
                        
                        view = ui.View()
                        other_options_button = ui.Button(style=discord.ButtonStyle.secondary, label="Outras opções")
                        async def other_options_callback(interaction: discord.Interaction):
                            if interaction.user.id != user_id:
                                await interaction.response.send_message("Você não pode usar este botão!", ephemeral=True)
                                return
                            
                            other_options_embed = discord.Embed(title="Outras Possíveis Respostas")
                            
                            # Limita as opções a um máximo de 5
                            for i, (s, path) in enumerate(results[1:6], start=1):
                                name = os.path.splitext(os.path.basename(path))[0]
                                other_options_embed.add_field(name=name, value=f"Similaridade: {s * 100:.2f}%", inline=False)

                            await interaction.response.send_message(embed=other_options_embed, ephemeral=True)

                        other_options_button.callback = other_options_callback
                        view.add_item(other_options_button)
                        await interaction.followup.send(f"# <@{user_id}> {' '.join(img_name.split()[1:])}", embed=embed, file=file, view=view)
                        
                    else:
                        await interaction.followup.send("Imagem original não encontrada.")
                    
                    # Move a imagem para a pasta de treinamento
                    training_dir = os.path.join(theme_dir, "imagens_treinamento")
                    os.makedirs(training_dir, exist_ok=True)
                    new_filename = self.safe_filename(f"treinamento_{img_name}.png")
                    new_path = os.path.join(training_dir, new_filename)

                    # Verifica se o arquivo já existe e adiciona um número sequencial se necessário
                    count = 1
                    base_name, ext = os.path.splitext(new_filename)
                    while os.path.exists(new_path):
                         new_filename = f"{base_name} {count:04}{ext}"
                         new_path = os.path.join(training_dir, new_filename)
                         count += 1

                    os.rename(training_image_path, new_path)  # Move a imagem
                    print(f"Imagem movida para {new_path}")
                else:
                      await interaction.followup.send("Não foi possível identificar a imagem.")
               
            except asyncio.TimeoutError:
                await interaction.followup.send("Tempo limite para resposta da imagem esgotado.", ephemeral=True)
            except Exception as e:
                 print(f"Erro ao monitorar a imagem de coach: {e}")
                 traceback.print_exc()
                 await interaction.followup.send("Erro ao processar a imagem do coach.", ephemeral=True)

    async def process_training_setup(self, interaction, user_id, guild_id, channel_id, theme_name):
        """Configura o processo de treinamento após a configuração do modal."""

        # Obtém o objeto channel para monitorar
        channel_to_monitor = self.bot.get_channel(channel_id)

        # Verifica as permissões do BOT no canal que será monitorado, a menos que seja uma DM
        if isinstance(channel_to_monitor, discord.TextChannel):
            if interaction.guild:  # Verifica se está em um servidor
                perms = channel_to_monitor.permissions_for(interaction.guild.me) # pega a permissão do bot
                if not (perms.read_messages and perms.read_message_history):
                    await interaction.followup.send("Eu não tenho permissão para ver este canal ou o histórico de mensagens.", ephemeral=True)
                    self.processing.discard(user_id)
                    return
            else:
                # Se estiver em DM, o bot tem permissão por padrão
                pass
        elif isinstance(channel_to_monitor, discord.DMChannel):
            # Não precisa verificar permissões em DMs
            pass
        else:  # Se não for TextChannel nem DM retorna
            await interaction.followup.send("Tipo de canal inválido. Use um canal de texto ou uma DM.", ephemeral=True)
            self.processing.discard(user_id)
            return

        try:
            await self.process_training(interaction, interaction.channel, channel_to_monitor, theme_name, user_id) # Usando ctx.channel para a mensagem de resposta e o canal_to_monitor para o monitoramento
        except Exception as e:
            await interaction.followup.send(f"Ocorreu um erro durante o treinamento: {e}", ephemeral=True)


    @commands.command(name="treinamento")
    async def treinamento(self, ctx: commands.Context):
        if ctx.author.id in self.processing:
            await ctx.send("Você já está em modo de treinamento. Finalize o processo atual antes de começar outro.", ephemeral=True)
            return

        self.processing.add(ctx.author.id)

        # Embed inicial
        embed = discord.Embed(
            title="Modo de Treinamento",
            description="Serei sua treinadora para aprender um tema. Clique no botão 'Configurar' abaixo para preencher as informações necessárias.",
            color=discord.Color.blue()
        )
        config_button = ui.Button(style=discord.ButtonStyle.primary, label="Configurar")

        # Callback do botão de configuração
        async def config_callback(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Você não pode usar este botão!", ephemeral=True)
                return

            modal = self.TrainingConfigModal(self)  # Passa a referência 'self' (a instância do cog)
            await interaction.response.send_modal(modal)
            # Espera o envio do modal
            await modal.wait()

            # Após o modal ser submetido, os dados estarão em self.training_configs
            if interaction.user.id in self.training_configs:
                # Já vai ser processado em on_submit do modal
                pass

        config_button.callback = config_callback
        view = ui.View()
        view.add_item(config_button)
        await ctx.send(embed=embed, view=view)

    async def process_training(self, interaction, response_channel, channel_to_monitor, theme_name, user_id):
         # Inicializa as variáveis
        training_image_path = None
        correct_answer = None
        last_message_id = None  # ID da última mensagem processada (inicialmente None)
        last_interval_message_id = None # ID da última mensagem de intervalo processada
        current_image_name = None
        processing_image = False  # Flag para controlar se estamos processando uma imagem
        image_start_time = None  # Para rastrear o início do processamento da imagem

        # Cria o diretório "Imagens Treinamento" se ele não existir
        training_dir = os.path.join(self.BASE_DIR, "Imagens Treinamento")
        os.makedirs(training_dir, exist_ok=True)

        theme_dir = os.path.join(self.BASE_DIR, theme_name)
        os.makedirs(theme_dir, exist_ok=True)

        theme_images_dir = os.path.join(theme_dir, f"imagens_{theme_name}_com_borda")
        os.makedirs(theme_images_dir, exist_ok=True)

        def is_interval_embed_with_result(embed):
            """Verifica se o embed é um embed de intervalo com resposta correta ou incorreta."""
            if not embed.footer or "Próxima imagem em" not in embed.footer.text:
                return False
            return "acertou:" in (embed.author.name or "") or "A resposta era:" in (embed.author.name or "")

        # Envia uma mensagem inicial para marcar o ponto de partida
        start_message = await response_channel.send("Início do monitoramento do treinamento.")
        last_message_id = start_message.id


        monitoring_image = False # flag para verificar se tá monintando uma imagem em si

         # Busca por um embed de intervalo nas mensagens recentes do bot do jogo
        interval_message = await self.find_initial_interval_embed(channel_to_monitor)
        if interval_message:
             last_interval_message_id = interval_message.id
             last_message_id = last_interval_message_id
        else:
            await response_channel.send("Não foi possível encontrar uma mensagem de intervalo inicial do bot do jogo. Iniciando o monitoramento do zero.")
        
        self.processed_messages.clear()  # Limpa as mensagens processadas ao iniciar o treinamento

        while user_id in self.processing:  # Continua enquanto o usuário estiver no modo de treinamento
            try:
                # Obtém as mensagens mais recentes após a última mensagem processada
                new_messages = []
                async for message in channel_to_monitor.history(limit=15, after=discord.Object(id=last_message_id)):
                    new_messages.append(message)

                new_messages.reverse()  # Processa na ordem correta (do mais antigo para o mais recente)

                for message in new_messages:
                    if message.id in self.processed_messages:
                        continue  # Ignora mensagens já processadas
                    
                    last_message_id = message.id  # Atualiza o ID da última mensagem processada
                    self.processed_messages.add(message.id) # Adiciona o ID ao conjunto de processadas
                    # Verifica se é uma mensagem do bot do jogo
                    if message.author.id == self.GAME_BOT_ID:
                    
                        # Verifica se há embed de imagem de jogo
                        if message.embeds:
                            embed = message.embeds[0]
                            if embed.fields and any("Vidas" in field.name for field in embed.fields) and embed.image:
                                monitoring_image = True # achou imagem, começa a monitorar ela
                                print("Encontrou embed de imagem de jogo")
                                processing_image = True # Indica que começou a processar uma imagem
                                image_start_time = datetime.now() # Armazena o tempo do inicio
                                image_url = embed.image.url
                                response = requests.get(image_url, stream=True)
                                response.raise_for_status()
                                image = Image.open(BytesIO(response.content))

                                # Salva a imagem do jogo na pasta com borda
                                file_name = f"{user_id}_consulta"
                                training_image_path = os.path.join(theme_images_dir, f"{file_name}.png")
                                image.save(training_image_path)

                                # Adiciona borda à imagem
                                bordered_image = self.add_border(training_image_path, theme_name)
                                if bordered_image:
                                    bordered_image.save(training_image_path)  # Salva a imagem com borda

                                # Compara a imagem com as outras na pasta com borda
                                results = self.compare_images(theme_images_dir, training_image_path)

                                if results:
                                    score, img_path = results[0]  # Maior similaridade
                                    current_image_name = os.path.splitext(os.path.basename(img_path))[0] # Salva o nome da imagem atual
                                    img_name = current_image_name
                                    similarity_percentage = score * 100 # Converte a similaridade em porcentagem

                                    # Encontra a imagem original (sem borda)
                                    original_image_path = os.path.join(theme_dir, f"{img_name}.png")  # Adapte a extensão se necessário
                                    if not os.path.exists(original_image_path):
                                        original_image_path = os.path.join(theme_dir, f"{img_name}.jpg")
                                    if not os.path.exists(original_image_path):
                                        original_image_path = os.path.join(theme_dir, f"{img_name}.jpeg")

                                    if os.path.exists(original_image_path):
                                        file = discord.File(original_image_path, filename="image.png")
                                        embed = discord.Embed(
                                            title="Resultado da Identificação",
                                            description=f"Similaridade: {similarity_percentage:.2f}%\n\nNão é a resposta? clique no botão abaixo para ver outras possíveis respostas", # Mostra o nome da imagem e a porcentagem
                                        )
                                        embed.set_thumbnail(url=f"attachment://image.png") # Adiciona a imagem como thumbnail
                                        
                                        # Calcula o tempo decorrido
                                        time_elapsed = datetime.now() - image_start_time
                                        seconds = time_elapsed.total_seconds()
                                        minutes = int(seconds // 60)  # Quantidade de minutos completos
                                        remaining_seconds = seconds % 60  # Segundos restantes

                                        embed.add_field(name="Tempo de Processamento", value=f"{minutes}m {remaining_seconds:.2f}s", inline=False)
                                        
                                        view = ui.View()
                                        other_options_button = ui.Button(style=discord.ButtonStyle.secondary, label="Outras opções")
                                        async def other_options_callback(interaction: discord.Interaction):
                                            if interaction.user.id != user_id:
                                                await interaction.response.send_message("Você não pode usar este botão!", ephemeral=True)
                                                return
                                            
                                            other_options_embed = discord.Embed(title="Outras Possíveis Respostas")
                                            
                                            # Limita as opções a um máximo de 5
                                            for i, (s, path) in enumerate(results[1:6], start=1):
                                                name = os.path.splitext(os.path.basename(path))[0]
                                                other_options_embed.add_field(name=name, value=f"Similaridade: {s * 100:.2f}%", inline=False)

                                            await interaction.response.send_message(embed=other_options_embed, ephemeral=True)

                                        other_options_button.callback = other_options_callback
                                        view.add_item(other_options_button)
                                        await response_channel.send(f"# <@{user_id}> {' '.join(img_name.split()[1:])}", embed=embed, file=file, view=view)
                                        
                                    else:
                                        await response_channel.send("Imagem original não encontrada.")

                                    # Move a imagem para a pasta de treinamento
                                    training_dir = os.path.join(theme_dir, "imagens_treinamento")
                                    os.makedirs(training_dir, exist_ok=True)
                                    new_filename = self.safe_filename(f"treinamento_{img_name}.png")
                                    new_path = os.path.join(training_dir, new_filename)

                                    # Verifica se o arquivo já existe e adiciona um número sequencial se necessário
                                    count = 1
                                    base_name, ext = os.path.splitext(new_filename)
                                    while os.path.exists(new_path):
                                         new_filename = f"{base_name} {count:04}{ext}"
                                         new_path = os.path.join(training_dir, new_filename)
                                         count += 1

                                    os.rename(training_image_path, new_path)  # Move a imagem
                                    print(f"Imagem movida para {new_path}")
                                else:
                                    await response_channel.send("Não foi possível identificar a imagem.")
                        # Verifica o embed de intervalo APÓS o último embed de imagem
                        elif is_interval_embed_with_result(embed) and monitoring_image == True:
                            monitoring_image = False # terminou de monitorar imagem, espera a próxima
                            print("Encontrou embed de intervalo para obter a resposta")
                            author_name = embed.author.name
                            if "acertou:" in author_name:
                                correct_answer = author_name.split("acertou:")[1].strip()
                            elif "A resposta era:" in author_name:
                                correct_answer = author_name.split("A resposta era:")[1].strip()

                            if training_image_path and correct_answer:
                                 # Renomeia a imagem de treinamento com a resposta
                                 new_filename = f"treinamento resposta_{self.safe_filename(correct_answer)}.png"
                                 new_path = os.path.join(training_dir, new_filename)

                                 # Move a imagem para o diretório de treinamento
                                 os.rename(training_image_path, new_path)
                                 training_image_path = None
                                 correct_answer = None
                                 print(f"Imagem movida para o diretório de treinamento e renomeada: {new_filename}")
                            last_interval_message_id = message.id
                            last_message_id = last_interval_message_id
                            processing_image = False # Reseta a flag de processamento
                        elif is_interval_embed_with_result(embed):
                            last_interval_message_id = message.id
                            last_message_id = last_interval_message_id
                            processing_image = False # Reseta a flag de processamento

                        # Verifica o embed de fim de jogo
                        elif embed.title == "FIM DE JOGO":
                            print("Encontrou embed de fim de jogo, interrompendo o treinamento")
                            await response_channel.send("Fim de jogo detectado. Finalizando o treinamento.")
                            self.processing.discard(user_id)  # Remove o usuário do modo de treinamento
                            return  # Sai da função process_training
                await asyncio.sleep(0.2)  # Intervalo para evitar sobrecarga na API do Discord

            except Exception as e:
                print(f"Erro durante o processamento contínuo: {e}")
                traceback.print_exc() # Imprime o traceback completo para diagnóstico
                break # Interrompe o loop em caso de erro grave

        await response_channel.send("Monitoramento do treinamento finalizado.")

    async def find_initial_interval_embed(self, channel):
        """Procura por um embed de intervalo nas últimas mensagens do bot do jogo."""
        messages = []
        async for message in channel.history(limit=10):
          if message.author.id == self.GAME_BOT_ID:
            messages.append(message)

        for message in reversed(messages): # verifica na ordem cronológica certa
            if message.embeds and self.is_interval_embed_with_result(message.embeds[0]):
                return message
        return None
    
    def is_interval_embed_with_result(self, embed):
        """Verifica se o embed é um embed de intervalo com resposta correta ou incorreta."""
        if not embed.footer or "Próxima imagem em" not in embed.footer.text:
            return False
        return "acertou:" in (embed.author.name or "") or "A resposta era:" in (embed.author.name or "")


    async def cog_unload(self):
        # Quando o cog é descarregado, limpa o conjunto de processing
        self.processing.clear()

async def setup(bot):
    await bot.add_cog(Treinamento(bot))