import discord
from discord import app_commands
from discord.ext import commands, tasks
import random
import datetime
import json
import os
import asyncio
import pytz  # Importe a biblioteca pytz

class BichoInteract(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        self.animal_emojis = {}
        self.all_animals = []
        self.daily_animals = []
        self.last_update = None
        self.config_ids = [400318261306195988, 497854782434705408]
        self.user_animals = {}
        self.data_file = "bicho_data.json"
        self.daily_result = None
        self.stats = {
            "total_palpites": 0,
            "acertos_principais": 0,
            "acertos_secundarios": 0,
            "erros": 0,
        }
        self.historical_results = {}
        try:
            self.load_data() #carrega os dados
        except Exception as e:
            print(f"Erro ao carregar dados iniciais: {e}")
            self.animal_emojis = {}
            self.all_animals = []
            self.daily_animals = []
            self.last_update = None
            self.user_animals = {}
            self.daily_result = None
            self.historical_results = {}

        self.all_animals = list(self.animal_emojis.keys()) #garante que self.all_animals seja preenchido após o load_data
        try:
            self.update_daily_animals() #atualiza os animais diários
        except Exception as e:
            print(f"Erro ao atualizar animais diários: {e}")
            self.daily_animals = []  # Garante que daily_animals seja inicializado

        try:
            self.monitored_users = self.load_monitored_users()  # Carregar usuários monitorados do arquivo
        except Exception as e:
            print(f"Erro ao carregar usuários monitorados: {e}")
            self.monitored_users = {} #garante que self.monitored_users seja inicializado

        self.reset_monitored_users_task.start() #inicia a task de zerar os usuários monitorados

    def load_monitored_users(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    # Certifique-se de que o formato de monitored_users está correto ao carregar
                    return data.get('monitored_users', {})
            else:
                print(f"Arquivo {self.data_file} não encontrado.")
                return {}
        except FileNotFoundError:
            print(f"Arquivo {self.data_file} não encontrado.")
            return {}
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON no arquivo {self.data_file}: {e}")
            return {}
        except Exception as e:
            print(f"Erro ao carregar usuários monitorados: {e}")
            return {}

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.animal_emojis = data.get('animal_emojis', {})
                    self.daily_animals = data.get('daily_animals', [])
                    self.last_update = datetime.datetime.fromisoformat(data.get('last_update')) if data.get('last_update') else None
                    
                    user_animals_data = data.get('user_animals', {})
                    self.user_animals = {}
                    for user_id_str, user_data in user_animals_data.items():
                       
                        user_id = int(user_id_str)
                        self.user_animals[user_id] = {
                            "animals": user_data.get('animals', []),
                            "time": datetime.datetime.fromisoformat(user_data.get('time')) if user_data.get('time') else None
                        }
                    self.daily_result = data.get('daily_result')
                    self.stats = data.get('stats', self.stats)
                    self.historical_results = data.get("historical_results",{})
                    

                    #validando todos os usuários na inicialização
                    for user_id in self.user_animals.keys():
                        if not self.check_user_animals_validity(user_id):
                            self.generate_user_animals(user_id, 16)
            else:
                print(f"Arquivo {self.data_file} não encontrado.")
                self.animal_emojis = {}
                self.all_animals = []
                self.daily_animals = []
                self.last_update = None
                self.user_animals = {}
                self.daily_result = None
                self.historical_results = {}

        except FileNotFoundError:
            print(f"Arquivo {self.data_file} não encontrado.")
            self.animal_emojis = {}
            self.all_animals = []
            self.daily_animals = []
            self.last_update = None
            self.user_animals = {}
            self.daily_result = None
            self.historical_results = {}
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON no arquivo {self.data_file}: {e}")
            self.animal_emojis = {}
            self.all_animals = []
            self.daily_animals = []
            self.last_update = None
            self.user_animals = {}
            self.daily_result = None
            self.historical_results = {}
        except Exception as e:
            print(f"Erro ao carregar dados do arquivo: {e}")
            self.animal_emojis = {}
            self.all_animals = []
            self.daily_animals = []
            self.last_update = None
            self.user_animals = {}
            self.daily_result = None
            self.historical_results = {}

    def save_data(self):
        user_animals_data = {}
        for user_id, user_data in self.user_animals.items():
          user_animals_data[user_id] = {
              "animals": user_data['animals'],
              "time": user_data['time'].isoformat() if user_data['time'] else None
          }
        data = {
            'animal_emojis': self.animal_emojis,
            'daily_animals': self.daily_animals,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'user_animals': user_animals_data,
            'daily_result': self.daily_result,
            'stats': self.stats,
            'historical_results': self.historical_results,
            'monitored_users': self.monitored_users
        }
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar dados no arquivo: {e}")

    def update_daily_animals(self):
        now = datetime.datetime.now()
        if self.last_update is None or self.last_update.date() < now.date():
            if not self.all_animals:
                print("Erro: self.all_animals está vazio. Não é possível selecionar animais diários.")
                return  # Ou lance uma exceção, dependendo da sua lógica
            self.daily_animals = random.sample(self.all_animals, min(16, len(self.all_animals)))  # Garante que não seja maior que a população
            self.last_update = now
            self.daily_result = None
            print(f"Animais diários atualizados: {self.daily_animals}")
            self.user_animals = {} # Limpando os animais do usuário aqui
            self.save_data()
        elif self.last_update.date() == now.date() : # adicionado a verificação do dia
            if not self.daily_animals:
                if not self.all_animals:
                    print("Erro: self.all_animals está vazio. Não é possível selecionar animais diários.")
                    return  # Ou lance uma exceção, dependendo da sua lógica
                self.daily_animals = random.sample(self.all_animals, min(16, len(self.all_animals)))  # Garante que não seja maior que a população
                self.save_data()

    def check_user_animals_validity(self, user_id):
      now = datetime.datetime.now()
      if user_id in self.user_animals and self.user_animals[user_id].get('time'):
          last_generated = self.user_animals[user_id].get('time')
          if last_generated and (last_generated.date() < now.date() or last_generated.hour >= 23):
              return False
          if user_id in self.user_animals and self.user_animals[user_id]['animals'] and  not all(animal in self.all_animals for animal in self.user_animals[user_id]['animals']):
              return False

      return True

    def generate_user_animals(self, user_id, quantidade):
        if quantidade > 16:
            quantidade = 16
        now = datetime.datetime.now()
        if not self.all_animals:
            print("Erro: self.all_animals está vazio. Não é possível gerar animais para o usuário.")
            return []  # Ou lance uma exceção
        self.user_animals[user_id] = {
            "animals": random.sample(self.all_animals, min(quantidade, len(self.all_animals))),
            "time": now
        }
        self.save_data()
        return self.user_animals[user_id]["animals"]

    def format_animals_to_embed(self, animals, title):
        embed = discord.Embed(title=title, color=discord.Color.purple())
        animals_text = ""
        for animal in animals:
            animals_text += f"{self.animal_emojis[animal]} {animal}\n"
        embed.add_field(name="Animais", value=animals_text)
        return embed
    
    async def send_daily_animals(self, interaction):
        embed = discord.Embed(title="Animais do Dia", color=discord.Color.blue())
        field1_text = ""
        for i, animal in enumerate(self.daily_animals):
          if i < 8:
            field1_text += f"{self.animal_emojis[animal]} {animal}\n"
        embed.add_field(name="Animais", value=field1_text, inline=True)
        return embed

    async def send_full_daily_animals(self, interaction):
        embed = discord.Embed(title="Animais do Dia", color=discord.Color.blue())
        field1_text = ""
        field2_text = ""
        for i, animal in enumerate(self.daily_animals):
            if i < 8:
              field1_text += f"{self.animal_emojis[animal]} {animal}\n"
            else:
              field2_text += f"{self.animal_emojis[animal]} {animal}\n"
        embed.add_field(name="Principais", value=field1_text, inline=True)
        embed.add_field(name="Secundários", value=field2_text, inline=True)
        return embed

    async def send_full_user_animals(self, interaction, user_id):
        if not self.check_user_animals_validity(user_id):
            user_animals = self.generate_user_animals(user_id, 16)
        elif user_id in self.user_animals:
            user_animals = self.user_animals[user_id]['animals']
        else:
            user_animals = self.generate_user_animals(user_id, 16)
        
        embed = discord.Embed(title="Seus Animais", color=discord.Color.purple())
        field1_text = ""
        field2_text = ""
        for i, animal in enumerate(user_animals):
            if i < 8:
                field1_text += f"{self.animal_emojis[animal]} {animal}\n"
            else:
                field2_text += f"{self.animal_emojis[animal]} {animal}\n"
        embed.add_field(name="Principais", value=field1_text, inline=True)
        embed.add_field(name="Secundários", value=field2_text, inline=True)
        return embed
    
    def check_result(self, result_animal):
        self.stats['total_palpites'] += 1
        if result_animal in self.daily_animals[:8]:
            self.stats['acertos_principais'] += 1
            return "Acertou! O animal estava entre os principais."
        elif result_animal in self.daily_animals[8:]:
            self.stats['acertos_secundarios'] += 1
            return "Quase! O animal estava entre os secundários."
        else:
            self.stats['erros'] += 1
            return "Errou! O animal não estava entre os palpites do dia."
    
    async def extract_animals_from_embed(self, embed):
        """Extrai os animais apostados do embed do bot."""
        animals = []
        for field in embed.fields:
            if field.name == "Suas apostas":
                lines = field.value.split("\n")
                for line in lines:
                    parts = line.split("`")  # Divide a linha em partes usando o caractere ` como separador
                    if len(parts) >= 2:
                        animal_name = parts[1].strip()  # Extrai o nome do animal, removendo espaços extras
                        animals.append(animal_name)
        return animals

    async def create_monitored_user_embed(self, user_id):
        """Cria um embed com os últimos animais apostados pelo usuário monitorado."""
        if user_id not in self.monitored_users or not self.monitored_users[user_id]["animals"]:
            return discord.Embed(title="Animais Apostados", description="Nenhuma aposta encontrada.", color=discord.Color.light_grey())

        animals = self.monitored_users[user_id]["animals"]
        embed = discord.Embed(title="Animais Apostados", color=discord.Color.green())
        animal_text = ""
        for animal in animals:
            animal_text += f"{self.animal_emojis.get(animal, '')} {animal}\n"
        embed.add_field(name="Animais", value=animal_text)
        return embed

    @app_commands.command(name="palpite", description="Mostra o palpite do usuário monitorado.")
    async def palpite(self, interaction: discord.Interaction, usuario: str):
        await interaction.response.defer()

        try:
            user_id = int(usuario)
            user = self.bot.get_user(user_id)
            if user is None:
                user = discord.utils.find(lambda m: m.name.lower() == usuario.lower(), self.bot.users)
        except ValueError:
            user = discord.utils.find(lambda m: m.name.lower() == usuario.lower(), self.bot.users)

        if user is None:
            await interaction.followup.send("Usuário não encontrado.", ephemeral=True)
            return
        
        user_id = str(user.id) # Garante que user_id é uma string
        print(f"Comando /palpite executado para o usuário: {user.name} (ID: {user_id})")

        if user_id in self.monitored_users:
            print(f"Usuário {user_id} já está sendo monitorado.")
            embed = await self.create_monitored_user_embed(user_id)
            await interaction.followup.send(embed=embed)
        else:
            print(f"Iniciando monitoramento do usuário: {user.name} (ID: {user_id})")
            self.monitored_users[user_id] = {"animals": []}
            self.save_data()
            embed = await self.create_monitored_user_embed(user_id)
            await interaction.followup.send(embed=embed, content=f"Iniciando monitoramento de {user.name}.", ephemeral=True)

    @tasks.loop(time=datetime.time(hour=22, minute=0, tzinfo=pytz.timezone('America/Sao_Paulo')))
    async def reset_monitored_users_task(self):
        """Reseta as apostas dos usuários monitorados às 22:00 (horário de Brasília)."""
        print("Resentando as apostas dos usuários monitorados.")
        for user_id in self.monitored_users:
            self.monitored_users[user_id]["animals"] = []
        self.save_data()
        print("Apostas dos usuários monitorados resetadas com sucesso.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        #Iterando sobre os usuários monitorados para verificar se a mensagem é referente a algum deles.
        for user_id in self.monitored_users:
            user = self.bot.get_user(int(user_id))

            if message.author == user and message.content in [".bicho", ". bicho"]: #Verifica se o author da mensagem é o usuário monitorado
                print(f"Mensagem '.bicho' detectada do usuário monitorado: {user.name} (ID: {user_id})")
                try:
                    def check(m):
                        return m.author.id == 628120853154103316 and m.reference and m.reference.message_id == message.id and len(m.embeds) > 0

                    reply = await self.bot.wait_for('message', check=check, timeout=60)
                    embed = reply.embeds[0]
                    animals = await self.extract_animals_from_embed(embed)

                    self.monitored_users[user_id]["animals"] = animals
                    self.save_data()
                    print(f"Animais atualizados para o usuário monitorado {user.name}: {animals}")


                except asyncio.TimeoutError:
                    print(f"Nenhuma resposta encontrada para .bicho de {user.name}.")


    async def extract_animals_from_embed(self, embed):
        animals = []
        for field in embed.fields:
            if field.name == "Suas apostas":
                lines = field.value.split("\n")
                for line in lines:
                    parts = line.split("`")
                    if len(parts) >= 2:
                        animal_name = parts[1].strip()
                        animals.append(animal_name)
        print(f"Animais extraídos do embed: {animals}") #ADICIONADO
        return animals

    async def create_monitored_user_embed(self, user_id):
        if user_id not in self.monitored_users or not self.monitored_users[user_id]["animals"]:
            print(f"Nenhuma aposta encontrada para o usuário: {user_id}")
            return discord.Embed(title="Animais Apostados", description="Nenhuma aposta encontrada.", color=discord.Color.light_grey())

        animals = self.monitored_users[user_id]["animals"]
        embed = discord.Embed(title="Animais Apostados", color=discord.Color.green())
        animal_text = ""
        for animal in animals:
            animal_text += f"{self.animal_emojis.get(animal, '')} {animal}\n"
        embed.add_field(name="Animais", value=animal_text)
        return embed

    class CallView(discord.ui.View):
        def __init__(self, cog, interaction, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.cog = cog
            self.interaction = interaction
            self.original_embed = None
            self.config_button_added = False
            self.result_button_added = False
            self.current_state = "inicial"  # Estado inicial

            # Cria os botões UMA VEZ na inicialização
            self.call_do_dia_button = discord.ui.Button(label="Call do Dia", style=discord.ButtonStyle.blurple, custom_id="call_do_dia", row=0)
            self.para_mim_button = discord.ui.Button(label="Para Mim", style=discord.ButtonStyle.green, custom_id="para_mim", row=1)
            self.completa_button = discord.ui.Button(label="Completa", style=discord.ButtonStyle.blurple, custom_id="completa", row=0)
            self.completa_para_mim_button = discord.ui.Button(label="Completa", style=discord.ButtonStyle.blurple, custom_id="completa_para_mim", row=0)
            self.resultado_button = discord.ui.Button(label="Resultado", style=discord.ButtonStyle.red, custom_id="resultado", row=2)
            self.config_button = discord.ui.Button(label="Configurar", style=discord.ButtonStyle.grey, custom_id="configurar", row=2)

            # Define as funções de callback dos botões
            self.call_do_dia_button.callback = self.call_do_dia_callback
            self.para_mim_button.callback = self.para_mim_callback
            self.completa_button.callback = self.completa_callback
            self.completa_para_mim_button.callback = self.completa_para_mim_callback
            self.resultado_button.callback = self.resultado_callback
            self.config_button.callback = self.config_callback
            
            self.add_initial_buttons()  # Adiciona os botões iniciais

        def add_initial_buttons(self):
            self.call_do_dia_button.row = 0  # Garante que o botão esteja na linha 0
            self.add_item(self.call_do_dia_button)

            self.para_mim_button.row = 0  # Move o botão "Para Mim" para a linha 1
            self.add_item(self.para_mim_button)

            if self.interaction.user.id in self.cog.config_ids:
                self.config_button.row = 1  # Move o botão "Configurar" para a linha 2
                self.add_item(self.config_button)

        async def update_view(self, interaction: discord.Interaction):
            self.clear_items()  # Limpa todos os botões

            # Adiciona os botões corretos com base no estado atual
            if self.current_state == "inicial":
                self.add_initial_buttons()
            elif self.current_state == "call_do_dia":
                self.completa_button.row = 0
                self.add_item(self.completa_button)

                self.para_mim_button.row = 0
                self.add_item(self.para_mim_button)

                self.resultado_button.row = 1

                self.add_item(self.resultado_button)
            elif self.current_state == "para_mim":
                self.completa_para_mim_button.row = 0
                self.add_item(self.completa_para_mim_button)

                self.resultado_button.row = 1
                self.add_item(self.resultado_button)

            await interaction.response.defer()  # Responde à interação
            await interaction.message.edit(view=self)  # Edita a mensagem com os novos botões

        async def on_interaction(self, interaction: discord.Interaction):
            """Verifica se o usuário que interage é o mesmo que invocou o comando."""
            if interaction.user != self.interaction.user:
                await interaction.response.send_message("Você não pode interagir com esse botão.", ephemeral=True)
                return False
            return True

        # Define as funções de callback dos botões
        async def call_do_dia_callback(self, interaction: discord.Interaction):
            if not await self.on_interaction(interaction):
                return

            embed = await self.cog.send_daily_animals(interaction)
            self.current_state = "call_do_dia"
            await self.update_view(interaction)
            await interaction.message.edit(embed=embed, view=self)
        
        async def para_mim_callback(self, interaction: discord.Interaction):
            if not await self.on_interaction(interaction):
                return
         
            user_id = interaction.user.id
            if not self.cog.check_user_animals_validity(user_id):
                user_animals = self.cog.generate_user_animals(user_id, 16)
            elif user_id in self.cog.user_animals:
                user_animals = self.cog.user_animals[user_id]["animals"]
            else:
                user_animals = self.cog.generate_user_animals(user_id, 16)

            embed = self.cog.format_animals_to_embed(user_animals[:8], "Seus Animais (Principais)")
            self.current_state = "para_mim"
            await self.update_view(interaction)
            await interaction.message.edit(embed=embed, view=self)

        async def completa_callback(self, interaction: discord.Interaction):
            if not await self.on_interaction(interaction):
                return
            embed = await self.cog.send_full_daily_animals(interaction)
            await self.update_view(interaction)
            await interaction.message.edit(embed=embed, view=self)
    
        async def completa_para_mim_callback(self, interaction: discord.Interaction):
            if not await self.on_interaction(interaction):
                return
            user_id = interaction.user.id
            if user_id in self.cog.user_animals:
                user_animals = self.cog.user_animals[user_id]["animals"]
            else:
                user_animals = self.cog.generate_user_animals(user_id, 16)

            embed = self.cog.format_animals_to_embed(user_animals, "Seus Animais (Completa)")
            await self.update_view(interaction)
            await interaction.message.edit(embed=embed, view=self)

        async def resultado_callback(self, interaction: discord.Interaction):
            if not await self.on_interaction(interaction):
                return
            self.current_state = "inicial"
            await self.update_view(interaction)
            await interaction.message.edit(embed=self.original_embed, view=self)

        async def config_callback(self, interaction: discord.Interaction):
            if not await self.on_interaction(interaction):
                return
            if interaction.user.id in self.cog.config_ids:
                view = self.cog.ConfigView(self.cog, interaction)
                animal_list_str = "\n".join([f"{self.cog.animal_emojis.get(animal, '')} {animal}" for animal in self.cog.all_animals])
                embed = discord.Embed(
                    title="Configuração de Animais",
                    description=f"Animais atuais:\n{animal_list_str}",
                    color=discord.Color.green(),
                )
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                await interaction.response.send_message("Você não tem permissão para configurar os animais.", ephemeral=True)

    class ConfigView(discord.ui.View):
      def __init__(self, cog, interaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cog = cog
        self.interaction = interaction

      async def interaction_check(self, interaction: discord.Interaction) -> bool:
          if interaction.user != self.interaction.user:
            await interaction.response.send_message("Você não pode interagir com esse botão.", ephemeral=True)
            return False
          return True
          
      @discord.ui.button(label="Limpar Animais", style=discord.ButtonStyle.red, custom_id="clear_animals", row=0)
      async def clear_animals_button(self, interaction: discord.Interaction, button: discord.ui.Button):
          if interaction.user.id in self.cog.config_ids:
              self.cog.animal_emojis = {}
              self.cog.all_animals = []
              self.cog.daily_animals = []
              self.cog.save_data()
              await self.cog.load_data()
              await interaction.response.send_message("Todos os animais foram limpos.", ephemeral=True)
          else:
            await interaction.response.send_message("Você não tem permissão para limpar os animais.", ephemeral=True)

      @discord.ui.button(label="Adicionar Animal", style=discord.ButtonStyle.green, custom_id="add_animal", row=0)
      async def add_animal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.cog.config_ids:
            await interaction.response.send_message("Envie os animais no formato `<emoji> <Nome do animal>` (um por linha)", ephemeral=True)
            self.cog.add_animal_mode = True
        else:
            await interaction.response.send_message("Você não tem permissão para adicionar animais.", ephemeral=True)
    
      @discord.ui.button(label="Definir Resultado", style=discord.ButtonStyle.blurple, custom_id="set_result", row=0)
      async def set_result_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.cog.config_ids:
             await interaction.response.send_message("Envie a data (YYYY-MM-DD), o animal e a posição (principal ou secundario), (ex: `2024-12-20 Lobo principal`)", ephemeral=True)
             self.cog.add_historical_result_mode = True
        else:
          await interaction.response.send_message("Você não tem permissão para adicionar um resultado.", ephemeral=True)

    @app_commands.command(name="call", description="Interage com os animais.")
    async def call(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.update_daily_animals()
        
        embed = discord.Embed(title="Bicho do Dia", color=discord.Color.blue())

        if self.daily_result:
           result_message = self.check_result(self.daily_result)
           embed.add_field(name="Resultado de Hoje", value=f"{self.animal_emojis.get(self.daily_result, '')} {self.daily_result}\n{result_message}", inline=False)
        else:
             embed.add_field(name="Resultado de Hoje", value="Nenhum resultado definido ainda.", inline=False)
        stats = self.stats
        embed.add_field(name="Estatísticas de Palpites", value=(
            f"Total de Palpites: {stats['total_palpites']}\n"
            f"Acertos (Principais): {stats['acertos_principais']}\n"
            f"Acertos (Secundários): {stats['acertos_secundarios']}\n"
            f"Erros: {stats['erros']}"
        ), inline=False)
            
        view = self.CallView(self, interaction)
        view.original_embed = embed
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(BichoInteract(bot))