import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View, Button, Modal, TextInput
from typing import List, Optional

class GerenciadorMensagens(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autorizacoes = {} # {channel_id: [user_id1, user_id2]}  <- Alterado para armazenar por canal
        super().__init__()

    @commands.hybrid_command(name="gerenciamento", description="Gerencia as autorizacoes de canais para gerenciamento de mensagens.")
    @commands.has_permissions(manage_channels=True)  # Verifica permissão para gerenciar canais
    async def gerenciamento(self, ctx):
        """
        Comando para configurar as autorizacoes de gerenciamento de mensagens.
        """
        view = CanalSelectionView(self, ctx.guild)
        embed = discord.Embed(title="Gerenciamento de Canais", description="Selecione um canal para gerenciar.", color=discord.Color.blue())
        await ctx.send(embed=embed, view=view)

    async def _get_message(self, ctx, message_id: str = None) -> discord.Message | None:
        """Helper function to get a message, either by ID or from a reply."""
        if ctx.message.reference and ctx.message.reference.message_id:
            try:
                return await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except discord.NotFound:
                await ctx.send("Mensagem respondida não encontrada.")
                return None
            except discord.Forbidden:
                await ctx.send("Não tenho permissão para acessar a mensagem respondida.")
                return None

        if message_id:
            try:
                message_id = int(message_id)
                return await ctx.channel.fetch_message(message_id)
            except ValueError:
                await ctx.send("ID da mensagem inválido. Insira um número inteiro.")
                return None
            except discord.NotFound:
                await ctx.send("Mensagem não encontrada.")
                return None
            except discord.Forbidden:
                await ctx.send("Não tenho permissão para acessar essa mensagem.")
                return None
        else:
            await ctx.send("Você precisa responder a uma mensagem ou fornecer um ID.")
            return None

    @commands.hybrid_command(name="fixar", description="Fixa uma mensagem no canal.")
    async def fixar(self, ctx, message_id: str = None):
        """
        Fixa uma mensagem no canal, se o usuário tiver permissão.
        Pode ser usado respondendo a uma mensagem ou fornecendo o ID.
        """
        mensagem = await self._get_message(ctx, message_id)
        if not mensagem:
            return

        if self.tem_permissao(ctx.author.id, ctx.channel.id):
            try:
                await mensagem.pin()
                await ctx.send(f"Mensagem com ID `{mensagem.id}` fixada com sucesso!")
            except discord.Forbidden:
                await ctx.send("Não tenho permissão para fixar mensagens neste canal.")
            except discord.HTTPException:
                await ctx.send("Erro ao fixar a mensagem.")
        else:
            await ctx.send("Você não tem permissão para fixar mensagens neste canal.")

    @commands.hybrid_command(name="desafixar", description="Desafixa uma mensagem no canal.")
    async def desafixar(self, ctx, message_id: str = None):
        """
        Desafixa uma mensagem no canal, se o usuário tiver permissão.
        Pode ser usado respondendo a uma mensagem ou fornecendo o ID.
        """
        mensagem = await self._get_message(ctx, message_id)
        if not mensagem:
            return

        if self.tem_permissao(ctx.author.id, ctx.channel.id):
            try:
                await mensagem.unpin()
                await ctx.send(f"Mensagem com ID `{mensagem.id}` desafixada com sucesso!")
            except discord.Forbidden:
                await ctx.send("Não tenho permissão para desafixar mensagens neste canal.")
            except discord.HTTPException:
                await ctx.send("Erro ao desafixar a mensagem.")
        else:
            await ctx.send("Você não tem permissão para desafixar mensagens neste canal.")

    @commands.hybrid_command(name="excluir", description="Exclui uma mensagem no canal.")
    async def excluir(self, ctx, message_id: str = None):
        """
        Exclui uma mensagem no canal, se o usuário tiver permissão.
        Pode ser usado respondendo a uma mensagem ou fornecendo o ID.
        """
        mensagem = await self._get_message(ctx, message_id)
        if not mensagem:
            return

        if self.tem_permissao(ctx.author.id, ctx.channel.id):
            try:
                await mensagem.delete()
                await ctx.send(f"Mensagem com ID `{mensagem.id}` excluída com sucesso!")
            except discord.Forbidden:
                await ctx.send("Não tenho permissão para excluir mensagens neste canal.")
            except discord.HTTPException:
                await ctx.send("Erro ao excluir a mensagem.")
        else:
            await ctx.send("Você não tem permissão para excluir mensagens neste canal.")


    @commands.hybrid_command(name="excluir_quantidade", description="Exclui uma quantidade de mensagens.")
    async def excluir_quantidade(self, ctx, quantidade: int):
        """Exclui uma quantidade de mensagens no canal."""
        if not self.tem_permissao(ctx.author.id, ctx.channel.id):
            await ctx.send("Você não tem permissão para excluir mensagens neste canal.")
            return

        if not (1 <= quantidade <= 100):
            await ctx.send("A quantidade de mensagens a excluir deve estar entre 1 e 100.")
            return

        try:
            await ctx.channel.purge(limit=quantidade + 1)  # +1 para excluir a mensagem do comando
            await ctx.send(f"{quantidade} mensagens excluídas com sucesso!", delete_after=5)
        except discord.Forbidden:
            await ctx.send("Não tenho permissão para excluir mensagens neste canal.")
        except discord.HTTPException as e:
            await ctx.send(f"Erro ao excluir mensagens: {e}")


    def tem_permissao(self, user_id, channel_id):
        """
        Verifica se um usuário tem permissão para gerenciar mensagens em um canal.
        """
        user_id = int(user_id)
        channel_id = int(channel_id)

        if channel_id in self.autorizacoes and user_id in self.autorizacoes[channel_id]:
            return True
        return False

    def adicionar_autorizacao(self, channel_id, user_id):
        """
        Adiciona a autorização para um usuário gerenciar mensagens em um canal.
        """
        channel_id = int(channel_id)
        user_id = int(user_id)

        if channel_id not in self.autorizacoes:
            self.autorizacoes[channel_id] = []

        if user_id not in self.autorizacoes[channel_id]:
            self.autorizacoes[channel_id].append(user_id)

    def remover_autorizacao(self, channel_id, user_id):
        """
        Remove a autorização para um usuário gerenciar mensagens em um canal.
        """
        channel_id = int(channel_id)
        user_id = int(user_id)

        if channel_id in self.autorizacoes and user_id in self.autorizacoes[channel_id]:
            self.autorizacoes[channel_id].remove(user_id)
            if not self.autorizacoes[channel_id]:
                del self.autorizacoes[channel_id]


class CanalSelectionView(View):
    def __init__(self, cog: GerenciadorMensagens, guild: discord.Guild):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild = guild
        self.channel_select = CanalSelect(cog, guild)  # Cria a instância aqui
        self.add_item(self.channel_select)

class CanalSelect(Select):
    def __init__(self, cog: GerenciadorMensagens, guild: discord.Guild): # Recebe o cog
        self.cog = cog
        self.guild = guild
        options = [
            discord.SelectOption(
                label=channel.name,
                value=str(channel.id),
                description=f"Canal: {channel.name}"
            )
            for channel in guild.text_channels
        ]

        # Discord limita Select menus a 25 opções e 5 componentes por view.
        if len(options) > 25:
            options = options[:25]  # Trunca para 25 opções

        super().__init__(
            placeholder="Selecione um canal...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="canal_select" # Necessário para persistir
        )


    async def callback(self, interaction: discord.Interaction):
        channel_id = int(self.values[0])
        channel = interaction.guild.get_channel(channel_id) # Usa interaction.guild
        view = GerenciamentoCanalView(self.cog, channel) # Passa o cog
        embed = view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

class GerenciamentoCanalView(View):
    def __init__(self, cog: GerenciadorMensagens, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.cog = cog
        self.channel = channel
        self.add_item(AddUserButton(cog, self))  # Passa o cog e self
        self.add_item(RemoveUserButton(cog, self)) # Passa o cog e self

    def create_embed(self):
        embed = discord.Embed(
            title=f"Gerenciamento do Canal: {self.channel.name}",
            color=discord.Color.green()
        )
        users_with_permission = self.cog.autorizacoes.get(self.channel.id, [])
        if users_with_permission:
            user_mentions = [f"<@{user_id}>" for user_id in users_with_permission]
            embed.add_field(
                name="Usuários com permissão:",
                value=", ".join(user_mentions),
                inline=False
            )
        else:
            embed.add_field(
                name="Usuários com permissão:",
                value="Nenhum usuário com permissão neste canal.",
                inline=False
            )
        return embed

class AddUserButton(Button):
    def __init__(self, cog: GerenciadorMensagens, view: GerenciamentoCanalView):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="Adicionar Usuário",
            custom_id="add_user_button"  # Necessário para persistir
        )
        self.cog = cog # Guarda o cog
        self.gerenciamento_canal_view = view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddUserModal(self.cog, self.gerenciamento_canal_view))  # Passa o cog

class RemoveUserButton(Button):
    def __init__(self, cog: GerenciadorMensagens, view: GerenciamentoCanalView):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Remover Usuário",
            custom_id="remove_user_button"  # Necessário para persistir
        )
        self.cog = cog # Guarda o cog
        self.gerenciamento_canal_view = view

    async def callback(self, interaction: discord.Interaction):
        users_with_permission = self.cog.autorizacoes.get(self.gerenciamento_canal_view.channel.id, [])
        if not users_with_permission:
            await interaction.response.send_message("Não há usuários para remover.", ephemeral=True)
            return

        # Cria um Select Menu com os usuários autorizados para remoção
        select_options = [discord.SelectOption(label=interaction.guild.get_member(user_id).name if interaction.guild.get_member(user_id) else f"Usuário Desconhecido ({user_id})", value=str(user_id)) for user_id in users_with_permission]
        remove_user_view = RemoveUserSelectView(self.cog, self.gerenciamento_canal_view, select_options) # Passa as opções para a nova View
        await interaction.response.send_message("Selecione o(s) usuário(s) para remover:", view=remove_user_view, ephemeral=True)


class AddUserModal(Modal, title='Adicionar Usuário'):
    def __init__(self, cog: GerenciadorMensagens, gerenciamento_canal_view: GerenciamentoCanalView):
        super().__init__()
        self.cog = cog
        self.gerenciamento_canal_view = gerenciamento_canal_view

    user_id = TextInput(label="ID/Nome do Usuário", placeholder="Insira o ID ou nome do usuário a ser adicionado")

    async def on_submit(self, interaction: discord.Interaction):
        user_identifier = self.user_id.value

        try:
            user_id = int(user_identifier)  # Tenta converter para ID
            user = interaction.guild.get_member(user_id)
            if not user:
                await interaction.followup.send("Usuário com este ID não encontrado.", ephemeral=True)
                return
        except ValueError:
            # Se não for um ID, tenta encontrar pelo nome
            users = [member for member in interaction.guild.members if member.name.lower() == user_identifier.lower()]
            if not users:
                await interaction.followup.send("Nenhum usuário encontrado com este nome.", ephemeral=True)
                return
            if len(users) > 1:
                await interaction.followup.send("Múltiplos usuários encontrados com este nome. Use o ID para ser mais específico.", ephemeral=True)
                return

            user = users[0]
            user_id = user.id

        self.cog.adicionar_autorizacao(self.gerenciamento_canal_view.channel.id, user_id)
        embed = self.gerenciamento_canal_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.gerenciamento_canal_view)
        try:
            await interaction.followup.send(f"Usuário <@{user_id}> adicionado ao canal <#{self.gerenciamento_canal_view.channel.id}>.", ephemeral=True)
        except discord.errors.InteractionResponded:
            await interaction.followup.send(f"Usuário <@{user_id}> adicionado ao canal <#{self.gerenciamento_canal_view.channel.id}>.", ephemeral=True)

class RemoveUserSelectView(View):
    def __init__(self, cog, gerenciamento_canal_view, select_options):
        super().__init__(timeout=None)
        self.cog = cog
        self.gerenciamento_canal_view = gerenciamento_canal_view
        self.remove_select = RemoveUserSelect(cog, gerenciamento_canal_view, select_options)
        self.add_item(self.remove_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

class RemoveUserSelect(Select):
    def __init__(self, cog, gerenciamento_canal_view, select_options):
        self.cog = cog
        self.gerenciamento_canal_view = gerenciamento_canal_view
        super().__init__(placeholder="Selecione os usuários para remover...", min_values=1, max_values=len(select_options), options=select_options, custom_id="remove_user_select")

    async def callback(self, interaction: discord.Interaction):
        for user_id in self.values:
            self.cog.remover_autorizacao(self.gerenciamento_canal_view.channel.id, int(user_id))

        embed = self.gerenciamento_canal_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.gerenciamento_canal_view)
        try:
            await interaction.followup.send(f"Usuários removidos do canal <#{self.gerenciamento_canal_view.channel.id}>.", ephemeral=True)
        except discord.errors.InteractionResponded:
            await interaction.followup.send(f"Usuários removidos do canal <#{self.gerenciamento_canal_view.channel.id}>.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(GerenciadorMensagens(bot))