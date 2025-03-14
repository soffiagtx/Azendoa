import discord
from discord.ext import commands
import random
from PIL import Image, ImageDraw, ImageFont
import asyncio
import re
import os
import json
from discord import ui
import logging
from discord.http import Route

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REACTIONS_SERVER_ID = 1304213764668784650
DATA_FILE = "reactions_data.json"
CONTENT_LOG_FILE = "content_log.txt"
CONTENT_COUNT_FILE = "content_count.json"


class TitleModal(ui.Modal, title="Definir Título"):
    def __init__(self):
        super().__init__()
        self.title_input = ui.TextInput(label="Título para o log", placeholder="Digite o título aqui", required=True, style=discord.TextStyle.short)
        self.add_item(self.title_input)
        self.modal_title = None  # Initialize title attribute

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # Added ephemeral=True
        self.modal_title = self.title_input.value  # Save the title
        self.interaction = interaction  # store interaction to edit later
        self.stop()


class ContentView(ui.View):
    def __init__(self, ctx: commands.Context, message_id: int):
        super().__init__()
        self.ctx = ctx
        self.message_id = message_id

    @ui.button(label="Título", style=discord.ButtonStyle.primary)
    async def title_button(self, interaction: discord.Interaction, button: ui.Button):
        modal = TitleModal()
        await interaction.response.send_modal(modal)
        await modal.wait()  # Wait for modal to be submitted

        if modal.modal_title is not None:
            embed = discord.Embed(title="Conteúdo da mensagem salva com sucesso!", color=discord.Color.green())
            embed.add_field(name="Título da mensagem", value=modal.modal_title, inline=False)
            embed.add_field(name="Usuário/Bot que enviou", value=self.ctx.author.mention, inline=False)  # Display author who used the command
            await interaction.followup.send(embed=embed, ephemeral=True)  # Send ephemeral message

            await self.call_conteudo_command(modal.modal_title, interaction)  # Pass interaction
        else:
            await interaction.message.edit(content="Nenhum título foi inserido.", view=None)

    async def call_conteudo_command(self, title_suffix, interaction: discord.Interaction):
        bot = self.ctx.bot
        conteudo_command = bot.get_command("conteúdo")
        await self.ctx.invoke(conteudo_command, message_id=self.message_id, title_suffix=title_suffix, interaction=interaction)  # Pass interaction


class Mensagens(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lista1 = []  # para suas reações temporárias
        self.lista2 = [400318261306195988]  # IDs com permissão para .reação
        self.usuarios_marcados = []
        self.reactions_data = self.load_reactions_data()  # Carrega dados de arquivo
        self.all_reactions = {}
        self.update_all_reactions()
        self.content_count = self.load_content_count()
        super().__init__()

    def load_reactions_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"servers": {}}

    def save_reactions_data(self):
        # Convert emoji objects to strings before saving
        for server_id, server_data in self.reactions_data["servers"].items():
            for global_name, global_emoji in server_data["global_reactions"].items():
                if isinstance(global_emoji, discord.Emoji):
                    server_data["global_reactions"][global_name] = str(global_emoji)
            for user_id, user_data in server_data["user_reactions"].items():
                for reaction_name, reaction_info in user_data.items():
                    if isinstance(reaction_info["emoji"], discord.Emoji):
                        user_data[reaction_name]["emoji"] = str(global_emoji)
                    elif isinstance(reaction_info["emoji"], discord.PartialEmoji):
                        user_data[reaction_name]["emoji"] = str(reaction_info["emoji"])

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.reactions_data, f, indent=4)

    def update_all_reactions(self):
        self.all_reactions = {}
        for server_id, server_data in self.reactions_data["servers"].items():
            for palavra, reacao in server_data["global_reactions"].items():
                self.all_reactions[palavra] = reacao
            for user_id, user_reactions in server_data["user_reactions"].items():
                for reaction_name, reaction_info in user_reactions.items():
                    self.all_reactions[reaction_name] = reaction_info["emoji"]

    def load_content_count(self):
        if os.path.exists(CONTENT_COUNT_FILE):
            with open(CONTENT_COUNT_FILE, "r") as f:
                return json.load(f)
        return {"count": 0}

    def save_content_count(self):
        with open(CONTENT_COUNT_FILE, "w") as f:
            json.dump(self.content_count, f, indent=4)

    def get_server_config(self, server_id):
        server_id = str(server_id)
        if server_id not in self.reactions_data["servers"]:
            self.reactions_data["servers"][server_id] = {
                "global_reactions": {},
                "user_reactions": {},
                "permissions": {"allowed_roles": [], "everyone": True},
                "global_names_chance": {}
            }
            self.save_reactions_data()
        return self.reactions_data["servers"][server_id]

# --------------------- Funções auxiliares -----------------------------

    def is_admin(self, user: discord.Member) -> bool:
        return user.guild_permissions.administrator
        
    def check_user_permission(self, user: discord.Member, server_config):
        if server_config["permissions"]["everyone"]:
            return True
        allowed_roles = server_config["permissions"]["allowed_roles"]
        for role in user.roles:
            if str(role.id) in allowed_roles:
                return True
        return False

    @commands.command(name="conteúdo", aliases=["conteudo"])
    async def conteudo_command(self, ctx: commands.Context, message_id: int, title_suffix: str = None, interaction: discord.Interaction = None):
        """
        Verifica e exibe o conteúdo de uma mensagem específica, incluindo embeds.

        Args:
            ctx: O contexto do comando.
            message_id: O ID da mensagem a ser verificada.
            title_suffix: O sufixo para o título do embed.
        """
        channel = ctx.channel

        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("Mensagem não encontrada.")
            return
        except discord.Forbidden:
            await ctx.send("Não tenho permissão para acessar este canal.")
            return
        except discord.HTTPException as e:
            await ctx.send(f"Erro ao buscar mensagem: {e}")
            return
        
        if title_suffix is None:
            view = ContentView(ctx, message_id)
            await ctx.send("Conteúdo será salvo, clique no botão abaixo para determinar um título", view=view)
            return

        self.content_count["count"] += 1
        self.save_content_count()

        embed = discord.Embed(title=f"Conteúdo da Mensagem (ID: {message_id})")
        embed.add_field(name="Conteúdo", value=message.content or "Nenhum", inline=False)

        has_embed = "Não contém embed" #default
        if message.embeds:
            has_embed = "Contém Embed"
            for i, original_embed in enumerate(message.embeds):
                embed_dict = original_embed.to_dict()
                embed_str = json.dumps(embed_dict, indent=4, ensure_ascii=False)  # Use json.dumps to format
                
                # Construct a dynamic embed title
                embed_title = title_suffix #Removed Embed #

                # Limit the embed_str to a maximum of 1024 characters to prevent issues with Discord's embed field limits.
                if len(embed_str) > 1024:
                    embed_str = embed_str[:1020] + " ..."

                embed.add_field(name=embed_title, value=f"```json\n{embed_str}\n```", inline=False)

                # Print the embed dictionary to the console
                print(f"{embed_title} Dictionary:")
                print(embed_dict)  # Print the dictionary to the console
                
                # Append data to the log file
                with open(CONTENT_LOG_FILE, "a", encoding="utf-8") as log_file:
                      log_file.write(f"Count: {self.content_count['count']}\n")
                      log_file.write(f"Message ID: {message_id}\n")
                      log_file.write(f"Title: {title_suffix}\n") #Just title suffix
                      log_file.write(f"Channel: {channel.name} ({channel.id})\n")
                      log_file.write(f"Message Content: {message.content}\n")
                      log_file.write(f"Embed data: \n{embed_str}\n\n")

        else:
            embed.add_field(name="Embeds", value="Nenhum", inline=False)
            
            # Append data to the log file even if there are no embeds
            with open(CONTENT_LOG_FILE, "a", encoding="utf-8") as log_file:
                log_file.write(f"Count: {self.content_count['count']}\n")
                log_file.write(f"Message ID: {message_id}\n")
                log_file.write(f"Title: {title_suffix}\n")#Just title suffix
                log_file.write(f"Channel: {channel.name} ({channel.id})\n")
                log_file.write(f"Message Content: {message.content}\n")
                log_file.write(f"Embed data: Nenhum embed encontrado.\n\n")
        
        if interaction:
            await interaction.edit_original_response(embed=embed)
        else:
            await ctx.send(embed=embed) # Fallback if no interaction available

    @commands.command(name="reacoes", aliases=["reações"])
    async def reacoes_command(self, ctx: commands.Context):
        if not self.is_admin(ctx.author) and ctx.author.id not in self.lista2:
            await ctx.send("Apenas administradores e desenvolvedores podem usar este comando.")
            return

        server_config = self.get_server_config(ctx.guild.id)

        view = ReacoesAdminView(self, ctx.guild.id)
        embed = discord.Embed(title="Gerenciar Reações", description="Reações cadastradas neste servidor")

        for name, reaction in server_config["global_reactions"].items():
            embed.add_field(name=name, value=str(reaction), inline=False)

        for user_id, data in server_config["user_reactions"].items():
            for reaction_name, reaction_info in data.items():
                user = self.bot.get_user(int(user_id))
                if user:
                    embed.add_field(name=f"Usuario {user.mention} {reaction_name}", value=str(reaction_info["emoji"]), inline=False)
                else:
                    embed.add_field(name=f"Usuario <@{user_id}> {reaction_name}", value=str(reaction_info["emoji"]), inline=False)

        if server_config["global_names_chance"]:
            names_str = "\n".join(f"{name}: {chance}" for name, chance in server_config["global_names_chance"].items())
            embed.add_field(name="Reações de nome", value=names_str, inline=False)

        await ctx.send(embed=embed, view=view)

    @commands.command(name="reação", aliases=["react", "reacao"])
    async def reacao_command(self, ctx: commands.Context):

        server_config = self.get_server_config(ctx.guild.id)
        if not self.check_user_permission(ctx.author, server_config):
            await ctx.send("Você não tem permissão para usar este comando.")
            return

        user_id = str(ctx.author.id)
        if user_id in server_config["user_reactions"] and server_config["user_reactions"][user_id]:
            view = ReacaoUserView(self, ctx.guild.id, user_id, is_edit=True)
            embed = discord.Embed(title="Minha Reação", description="Você já possui uma reação personalizada, deseja altera-la?")
            for reaction_name, reaction_info in server_config["user_reactions"][user_id].items():
                embed.add_field(name=reaction_name, value=str(reaction_info["emoji"]), inline=False)
            await ctx.send(embed=embed, view=view)
        else:
            view = ReacaoUserView(self, ctx.guild.id, user_id, is_edit=False)
            embed = discord.Embed(title="Minha Reação", description="Você ainda não possui reação personalizada, adicione uma!")
            await ctx.send(embed=embed, view=view)
        

# --------------------- Botões  -----------------------------
class ReacaoUserView(ui.View):
    def __init__(self, cog: Mensagens, server_id, user_id, is_edit=False):
        super().__init__()
        self.cog = cog
        self.server_id = server_id
        self.user_id = user_id
        self.is_edit = is_edit
        
        if is_edit:
             botao = ui.Button(label="Alterar", style=discord.ButtonStyle.blurple, custom_id="alterar")
             botao.callback = self.interaction
             self.add_item(botao)
        else:
            botao = ui.Button(label="Adicionar", style=discord.ButtonStyle.green, custom_id="adicionar")
            botao.callback = self.interaction
            self.add_item(botao)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == int(self.user_id)
    
    async def interaction(self, interaction: discord.Interaction):
      await interaction.response.send_modal(ReacaoNameModal(self.cog, self.server_id, self.user_id, is_edit=self.is_edit))
        
class ReacoesAdminView(ui.View):
    def __init__(self, cog: Mensagens, server_id):
        super().__init__()
        self.cog = cog
        self.server_id = server_id
    
    @ui.button(label="Apagar", style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, button: ui.Button):
        server_config = self.cog.get_server_config(self.server_id)
        
        all_reactions = []
        for name, reaction in server_config["global_reactions"].items():
            all_reactions.append(f"global:{name}")
        for user_id, user_reactions in server_config["user_reactions"].items():
            for reaction_name, reaction_info in user_reactions.items():
                  all_reactions.append(f"user:{user_id}:{reaction_name}")
        
        
        view = ReactionDeleteView(self.cog, self.server_id, all_reactions)
        await interaction.response.send_message("Selecione as reações que deseja remover:", view=view, ephemeral=True)
    
    @ui.button(label="Adicionar", style=discord.ButtonStyle.green)
    async def add(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ReacaoNameModal(self.cog, self.server_id))
    
    @ui.button(label="Permissões", style=discord.ButtonStyle.blurple)
    async def permissions(self, interaction: discord.Interaction, button: ui.Button):
         await interaction.response.send_modal(PermissionModal(self.cog, self.server_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.cog.is_admin(interaction.user)

class ReactionDeleteView(ui.View):
    def __init__(self, cog: Mensagens, server_id, reactions):
       super().__init__()
       self.cog = cog
       self.server_id = server_id
       self.reactions = reactions
       self.selected_reactions = []
       
       options = [discord.SelectOption(label=r.split(":")[-1], value=r) for r in self.reactions]
       if options:
           self.select = ui.Select(min_values=1, max_values=len(options), options=options)
           self.select.callback = self.select_callback
           self.add_item(self.select)
       self.confirm_button = ui.Button(label="Confirmar", style=discord.ButtonStyle.green)
       self.confirm_button.callback = self.confirm
       self.add_item(self.confirm_button)

    async def select_callback(self, interaction: discord.Interaction):
           self.selected_reactions = self.select.values
           
           embed = discord.Embed(title="Reações Selecionadas", description="Confirme a remoção das seguintes reações:")
           
           server_config = self.cog.get_server_config(self.server_id)
           for reaction in self.selected_reactions:
               parts = reaction.split(":")
               if parts[0] == "global":
                   name = parts[1]
                   embed.add_field(name=name, value="Reação global", inline=False)
               elif parts[0] == "user":
                  user_id = parts[1]
                  reaction_name = parts[2]
                  user = self.cog.bot.get_user(int(user_id))
                  if user:
                       embed.add_field(name=f"{reaction_name} do usuário: {user.mention}", value=f"Reação do usuário {user.name}", inline=False)
                  else:
                       embed.add_field(name=f"{reaction_name} do usuário <@{user_id}>", value="Reação de usuário", inline=False)

           await interaction.response.edit_message(content="", embed=embed, view=self)
           
           
    @ui.button(label="Voltar", style=discord.ButtonStyle.grey)
    async def voltar(self, interaction: discord.Interaction, button: ui.Button):
        
           options = [discord.SelectOption(label=r.split(":")[-1], value=r) for r in self.reactions]
           self.select = ui.Select(min_values=1, max_values=len(options), options=options)
           self.select.callback = self.select_callback
           self.clear_items()
           self.add_item(self.select)
           self.add_item(self.confirm_button)
           self.selected_reactions = []
           await interaction.response.edit_message(content="Selecione as reações que deseja remover:", view=self, embed=None)
           

    async def confirm(self, interaction: discord.Interaction):
        
      
       server_config = self.cog.get_server_config(self.server_id)

       for reaction in self.selected_reactions:
           parts = reaction.split(":")
           if parts[0] == "global":
                name = parts[1]
                if name in server_config["global_reactions"]:
                   del server_config["global_reactions"][name]
           elif parts[0] == "user":
                 user_id, reaction_name = parts[1], parts[2]
                 if user_id in server_config["user_reactions"] and reaction_name in server_config["user_reactions"][user_id]:
                     del server_config["user_reactions"][user_id][reaction_name]
                     if not server_config["user_reactions"][user_id]:
                         del server_config["user_reactions"][user_id]
       self.cog.save_reactions_data()
       self.update_all_reactions()
       await interaction.response.edit_message(content="Reações removidas com sucesso!", embed=None, view=None)
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.cog.is_admin(interaction.user)
      
class ReacaoNameModal(ui.Modal, title="Nome da Reação"):
    def __init__(self, cog: Mensagens, server_id, user_id=None, is_edit=False):
        super().__init__()
        self.cog = cog
        self.server_id = server_id
        self.user_id = user_id
        self.is_edit = is_edit
        self.name = ui.TextInput(label="Nome da Reação", placeholder="Ex: legal, legalzinho", required=True)
        self.add_item(self.name)
        if not user_id:
          self.user_id_input = ui.TextInput(label="ID do Usuário (Opcional)", placeholder="Deixe em branco se a reação for global", required=False)
          self.add_item(self.user_id_input)


    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Nome da reação: '{self.name.value}'. Agora, envie o emoji desejado, ou um link/imagem para usar como reação.", ephemeral=True)
        
        def check(msg):
              return msg.author == interaction.user and msg.channel == interaction.channel
        try:
            emoji_message = await self.cog.bot.wait_for("message", check=check, timeout=120) # espera até 120 segundos
            emoji_str = emoji_message.content
            if emoji_message.attachments:
                 await self.process_emoji(interaction, None, self.name.value, image_bytes=await emoji_message.attachments[0].read(), user_id_str = self.user_id_input.value if not self.user_id else self.user_id)
            else:
                await self.process_emoji(interaction, emoji_str, self.name.value, user_id_str = self.user_id_input.value if not self.user_id else self.user_id)
                
        except asyncio.TimeoutError:
            await interaction.followup.send("Tempo esgotado para enviar o emoji", ephemeral=True)

    async def process_emoji(self, interaction: discord.Interaction, emoji_str, reaction_name, image_bytes=None, user_id_str=None):
      
        emoji_custom = None
        
        try:
            servidor_emojis = self.cog.bot.get_guild(REACTIONS_SERVER_ID)
            if not image_bytes:
                emoji_obj = discord.PartialEmoji.from_str(emoji_str) if emoji_str else None
                if emoji_obj:
                    if hasattr(emoji_obj, 'asset'): # only fetch emojis that have an asset attribute
                        #  Use asset.url instead of emoji.url directly
                        image_url = str(emoji_obj.asset.url)
                        
                        try:
                            logging.info(f"Requesting image from URL: {image_url}")
                            route = Route("GET", image_url) # Create route with url to pass the parameter to http request
                            response = await self.cog.bot.http.request(route=route)
                            image_bytes = await response.read()
                        except Exception as e:
                            logging.error(f"Error fetching image from URL: {image_url}, error: {e}")
                            await interaction.followup.send(f"Erro ao obter imagem do emoji: {e}", ephemeral=True)
                            return
                        emoji_custom = await servidor_emojis.create_custom_emoji(name=reaction_name, image=image_bytes)
                        logging.info(f"Emoji customizado criado com sucesso: {emoji_custom}, nome:{reaction_name}")
                    else:
                        emoji_custom = str(emoji_obj)  # Keep the unicode or other non-custom emoji as a string
                        logging.info(f"Not a custom emoji, using directly: {emoji_custom}, nome:{reaction_name}")
                else:
                    await interaction.followup.send("Emoji/Link inválido.", ephemeral=True)
                    return
            else:
                logging.info(f"Using existing emoji or creating emoji from image, name: {reaction_name}, image_bytes: {bool(image_bytes)}")
                emoji_custom = await servidor_emojis.create_custom_emoji(name=reaction_name, image=image_bytes) # maintains normal emoji or creates an emoji from a provided image
                logging.info(f"Emoji customizado criado com sucesso: {emoji_custom}, nome:{reaction_name}")
        
            server_config = self.cog.get_server_config(self.server_id)

            if self.user_id and self.is_edit: # Alterar Reação de usuario
                 if str(self.user_id) not in server_config["user_reactions"]:
                    server_config["user_reactions"][str(self.user_id)] = {}
                 server_config["user_reactions"][str(self.user_id)] = {reaction_name: {"emoji": emoji_custom}}
            
            elif user_id_str and str(user_id_str).strip(): # Reacao por usuario
                user_id_str = str(user_id_str).strip()
                try:
                  user_id = int(user_id_str)
                except ValueError:
                  await interaction.followup.send("ID de usuário inválido.", ephemeral=True)
                  return
                
                if not self.cog.bot.get_user(user_id):
                     await interaction.followup.send("Usuário não encontrado no servidor.", ephemeral=True)
                     return
                
                if str(user_id) not in server_config["user_reactions"]:
                    server_config["user_reactions"][str(user_id)] = {}
                
                
                server_config["user_reactions"][str(user_id)][reaction_name] = {"emoji": emoji_custom}
                
            else:  # Reacao global
                server_config["global_reactions"][reaction_name] = emoji_custom
            
            self.cog.save_reactions_data()
            self.cog.update_all_reactions()
            await interaction.followup.send("Reação adicionada com sucesso!", ephemeral=True)
            logging.info(f"Reaction added successfully: {reaction_name}, emoji: {emoji_custom}")
        except Exception as e:
            logging.error(f"Error processing emoji: {e}")
            await interaction.followup.send(f"Erro ao adicionar reação: {e}", ephemeral=True)
        

class PermissionModal(ui.Modal, title="Configurar Permissões"):
    def __init__(self, cog: Mensagens, server_id):
       super().__init__()
       self.cog = cog
       self.server_id = server_id
       self.roles = ui.TextInput(label="Cargos permitidos (ID's separados por espaço)", placeholder="Se todos os membros podem adiconar deixe em branco", required=False)
       self.add_item(self.roles)
    
    async def on_submit(self, interaction: discord.Interaction):
       server_config = self.cog.get_server_config(self.server_id)
       
       if self.roles.value.strip():
         role_ids = self.roles.value.split()
         server_config["permissions"]["allowed_roles"] = role_ids
         server_config["permissions"]["everyone"] = False
       else:
           server_config["permissions"]["allowed_roles"] = []
           server_config["permissions"]["everyone"] = True
       
       self.cog.save_reactions_data()
       await interaction.response.send_message("Permissões atualizadas com sucesso!", ephemeral=True)

# --------------------- Listener de mensagens -----------------------------
    usuários_com_reação = {
        548819214606139403: {"display_name": "etoile", "reação": "<a:ihu:737366810248347799>"},
        283654977401126912: {"display_name": "coxinha", "reação": "<:coxinha:1225879435241197619>"},
        400318261306195988: {"display_name": "finn", "reação": "<a:bey_tururu:1217510268737945650>"}
    }
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.display_name != after.display_name:
            for user_id, data in self.usuários_com_reação.items():
                if data["display_name"] == before.display_name:
                    data["display_name"] = after.display_name
                    break

    @commands.command(name="marcar")
    async def marcar(self, ctx: commands.Context):
        if ctx.author.id in self.usuarios_marcados:
            await ctx.send("Você já está na lista de marcados.")
            return
        self.usuarios_marcados.append(ctx.author.id)
        await ctx.send(f"Você foi adicionado à lista de marcados.")

    @commands.command(name="desmarcar")
    async def desmarcar(self, ctx: commands.Context):
        if ctx.author.id in self.usuarios_marcados:
            self.usuarios_marcados.remove(ctx.author.id)
            await ctx.send(f"Você foi removido da lista de marcados.")
        else:
            await ctx.send("Você não está na lista de marcados.")
    
    nomes_com_chance = {
        "finn": 0.1,
        "aume": 0.3,
        "alme": 0.3,
        "leo": 0.3,
        "yuki": 0.3,
        "lipe": 0.3,
        "vaga": 0.3,
        "argo": 0.3,
        "dé": 0.3,
        "chell": 0.3,
        "cheli": 0.3,
        "allons": 0.3,
        "star": 0.1,
        "monico": 0.1,
        "dedé": 0.3,
        "kido": 0.3
    }

    @commands.Cog.listener()
    async def on_message(self, mensagem: discord.Message):
        autor = mensagem.author
        if autor.bot:
            return
        # Check 1: Verificar comandos .vet e .ver no canal específico
        if mensagem.channel.id == 1300879276416958546:
            palavras = mensagem.content.lower().split()
            if len(palavras) > 2 and (palavras[0] == ".vet" or palavras[0] == ".ver"):
                conteudo_restante = ' '.join(palavras[2:])
                resposta_base = f"# {conteudo_restante}"

                print("Resposta inicial enviada:", resposta_base)

                def check(msg):
                    return msg.author.id == 628120853154103316 and \
                        msg.channel.id == mensagem.channel.id and \
                        len(msg.embeds) > 0

                try:
                    resposta_bot = await self.bot.wait_for('message', timeout=3.0, check=check)
                    if resposta_bot:
                        # Improved check for content in embeds
                        found_content = False
                        for embed in resposta_bot.embeds:
                            if conteudo_restante.lower() in (embed.description or "").lower() or \
                                    conteudo_restante.lower() in (embed.title or "").lower():
                                found_content = True
                                break
                        # Check for image in embeds (at least one embed must have an image url)
                        has_image = any(embed.image.url for embed in resposta_bot.embeds)

                        if found_content and has_image:
                            print("Bot respondeu conforme esperado.")
                            for user_id in self.usuarios_marcados:
                                try:
                                    await mensagem.channel.send(f"{resposta_base} <@{user_id}>")
                                except discord.Forbidden:
                                    print(f"Could not send message to <@{user_id}> - Missing permissions.")
                        else:
                            print("Bot response did not contain expected content or image.")

                except asyncio.TimeoutError:
                    
                    print("O bot não respondeu conforme esperado.")
                except Exception as e:
                    print(f"An error occurred: {e}")

        server_config = self.get_server_config(mensagem.guild.id)
        # Check 2: Adicionar reações baseadas em nomes com chances
        
        if server_config["global_names_chance"]:
            for nome, chance in server_config["global_names_chance"].items():
                if nome in mensagem.content.lower():
                    numero_aleatorio = random.random()
                    if numero_aleatorio <= chance:
                       print(f"Reagindo com 🌈 ao encontrar o nome: {nome}")
                       await mensagem.add_reaction('🌈')
                       break

        # Check 3: Adicionar reações específicas baseadas em palavras-chave
        
        for palavra, reacao in self.all_reactions.items():
           if palavra in mensagem.content.lower():
                print(f"Reagindo com {reacao} à palavra-chave: {palavra} no servidor: {mensagem.guild.name}")
                await mensagem.add_reaction(reacao)
                break

        if "nove" in mensagem.content.lower():
            if "nove?" in mensagem.content.lower():
                print("Reagindo com <:99:1225879473392586843> para 'nove?'")
                await mensagem.add_reaction('<:99:1225879473392586843>')
            else:
                print("Reagindo com ❓ para 'nove'")
                await mensagem.add_reaction('❓')

    @commands.command()
    async def falar(self, ctx: commands.Context, *, frase: str):
        await ctx.message.delete()
        await ctx.send(frase)
        
async def setup(bot):
    await bot.add_cog(Mensagens(bot))