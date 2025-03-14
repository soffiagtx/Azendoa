import discord
from discord import app_commands
from discord.ext import commands
import random
import datetime
import json
import os


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
        self.load_data()
        self.update_daily_animals()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
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
                    self.all_animals = list(self.animal_emojis.keys())
                    
                    #validando todos os usuários na inicialização
                    for user_id in self.user_animals.keys():
                        if not self.check_user_animals_validity(user_id):
                            self.generate_user_animals(user_id, 16)
            except Exception as e:
                print(f"Erro ao carregar dados do arquivo: {e}")
                self.animal_emojis = {}
                self.all_animals = []
                self.daily_animals = []
                self.last_update = None
                self.user_animals = {}
                self.daily_result = None
                self.historical_results = {}
        else:
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
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def update_daily_animals(self):
        now = datetime.datetime.now()
        if self.last_update is None or self.last_update.date() < now.date():
            self.daily_animals = random.sample(self.all_animals, 16)
            self.last_update = now
            self.daily_result = None
            print(f"Animais diários atualizados: {self.daily_animals}")
            self.user_animals = {} # Limpando os animais do usuário aqui
            self.save_data()
        elif self.last_update.date() == now.date() : # adicionado a verificação do dia
            if not self.daily_animals:
              self.daily_animals = random.sample(self.all_animals, 16)
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
        self.user_animals[user_id] = {
            "animals": random.sample(self.all_animals, 16),
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

    class CallView(discord.ui.View):
        def __init__(self, cog, interaction, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.cog = cog
            self.interaction = interaction
            self.original_embed = None
            self.config_button_added = False
            self.result_button_added = False
            self.current_state = "inicial"  # Estado inicial
            

        
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.user != self.interaction.user:
                await interaction.response.send_message("Você não pode interagir com esse botão.", ephemeral=True)
                return False
            return True
        
        async def update_view(self, interaction):
           self.clear_items()
           if self.current_state == "inicial":
              self.add_item(self.call_do_dia_button)
              self.add_item(self.para_mim_button)
              if interaction.user.id in self.cog.config_ids:
                  self.add_item(self.config_button)
           elif self.current_state == "call_do_dia":
              self.add_item(self.completa_button)
              self.add_item(self.para_mim_button)
              self.add_item(self.resultado_button)
           elif self.current_state == "para_mim":
              self.add_item(self.completa_para_mim_button)
              self.add_item(self.resultado_button)
           
           await interaction.message.edit(view=self) # Use interaction.message.edit()
        
        @discord.ui.button(label="Call do Dia", style=discord.ButtonStyle.blurple, custom_id="call_do_dia", row=0)
        async def call_do_dia_button(self, interaction: discord.Interaction, button: discord.ui.Button):
             # Mostra os 8 primeiros animais do dia
            embed = await self.cog.send_daily_animals(interaction)
            self.current_state = "call_do_dia"
            await interaction.response.defer() # Responda a interação com um defer
            await self.update_view(interaction) # Atualize a view
            await interaction.message.edit(embed=embed) # Edite a mensagem com o novo embed
        


        @discord.ui.button(label="Para Mim", style=discord.ButtonStyle.green, custom_id="para_mim", row=0)
        async def para_mim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Mostra os 8 primeiros animais específicos do usuário
            user_id = interaction.user.id
            if not self.cog.check_user_animals_validity(user_id):
                 user_animals = self.cog.generate_user_animals(user_id, 16)
            elif user_id in self.cog.user_animals:
                user_animals = self.cog.user_animals[user_id]["animals"]
            else:
                user_animals = self.cog.generate_user_animals(user_id,16)

            embed = self.cog.format_animals_to_embed(user_animals[:8], "Seus Animais (Principais)")
            self.current_state = "para_mim"
            await interaction.response.defer()  # Responda a interação com um defer
            await self.update_view(interaction)
            await interaction.message.edit(embed=embed) # Edite a mensagem com o novo embed



        @discord.ui.button(label="Completa", style=discord.ButtonStyle.blurple, custom_id="completa", row=0)
        async def completa_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Mostra todos os 16 animais do dia
            embed = await self.cog.send_full_daily_animals(interaction)
            await interaction.response.defer()
            await interaction.message.edit(embed=embed, view=self)


        @discord.ui.button(label="Completa", style=discord.ButtonStyle.blurple, custom_id="completa_para_mim", row=0)
        async def completa_para_mim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Mostra todos os 16 animais específicos do usuário
           
            user_id = interaction.user.id
            if  user_id in self.cog.user_animals:
               user_animals = self.cog.user_animals[user_id]["animals"]
            else:
                user_animals = self.cog.generate_user_animals(user_id, 16)

            embed = self.cog.format_animals_to_embed(user_animals, "Seus Animais (Completa)")
            await interaction.response.defer()
            await interaction.message.edit(embed=embed, view=self)
        
        @discord.ui.button(label="Resultado", style=discord.ButtonStyle.red, custom_id="resultado", row=1)
        async def resultado_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Volta para o embed principal
            self.current_state = "inicial"
            await interaction.response.defer()
            await self.update_view(interaction)
            await interaction.message.edit(embed=self.original_embed)

        @discord.ui.button(label="Configurar", style=discord.ButtonStyle.grey, custom_id="configurar", row=0)
        async def config_button(self, interaction: discord.Interaction, button: discord.ui.Button):
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
    
    @commands.Cog.listener()
    async def on_message(self, message):
      if message.author.bot:
          return
      if message.author.id in self.config_ids:
          if hasattr(self, 'add_animal_mode') and self.add_animal_mode:
            
              lines = message.content.strip().split('\n')
              added_animals = []

              for line in lines:
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                  emoji, animal_name = parts
                  try:
                    await message.add_reaction(emoji)
                    self.animal_emojis[animal_name] = emoji
                    self.all_animals = list(self.animal_emojis.keys())
                    added_animals.append(f"Animal {animal_name} com emoji {emoji} adicionado.")
                    
                  except:
                      added_animals.append(f"Emoji inválido para: {animal_name}.")
                      
                else:
                  added_animals.append(f"Formato inválido na linha: {line}. Use `<emoji> <Nome do animal>`")
              
              await message.channel.send("\n".join(added_animals))
              self.save_data()
              await self.load_data()
              self.update_daily_animals()
              for user_id in self.user_animals.keys():
                 if not self.check_user_animals_validity(user_id):
                  self.generate_user_animals(user_id,16)
              
              self.add_animal_mode = False
          elif hasattr(self, 'add_historical_result_mode') and self.add_historical_result_mode:
             content = message.content.split()
             if len(content) >= 3:
                date_str = content[0]
                animal_name = " ".join(content[1:-1])
                position = content[-1]
                try:
                    datetime.datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                  await message.channel.send("Data inválida, use o formato AAAA-MM-DD")
                  self.add_historical_result_mode = False
                  return
                if position.lower() != "principal" and position.lower() != "secundario":
                   await message.channel.send("Posição inválida, use 'principal' ou 'secundario'")
                   self.add_historical_result_mode = False
                   return
                if animal_name not in self.all_animals:
                   await message.channel.send("Animal não encontrado.")
                   self.add_historical_result_mode = False
                   return
                if position.lower() == "principal":
                   message_result = "Acertou! O animal estava entre os principais."
                else:
                  message_result = "Quase! O animal estava entre os secundários."
                   
                self.historical_results[date_str] = {
                    "result": animal_name,
                    "position": position.lower(),
                    "message": message_result
                }
                await message.channel.send(f"Resultado histórico para {date_str} definido como {animal_name} - {position}.")
                self.save_data()
             else:
               await message.channel.send("Formato inválido. Use: `AAAA-MM-DD Animal principal/secundario`")
             self.add_historical_result_mode = False
          elif self.daily_result is None:
            result_animal = message.content
            if result_animal in self.all_animals:
                self.daily_result = result_animal
                self.save_data()
                await message.channel.send(f"Resultado do dia definido como: {self.animal_emojis.get(self.daily_result, '')} {self.daily_result}")
            

async def setup(bot):
    await bot.add_cog(BichoInteract(bot))