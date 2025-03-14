import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View

class GerenciadorMensagens(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autorizacoes = {} # {user_id: [channel_id1, channel_id2]}
        super().__init__()

    @commands.hybrid_command(name="gerenciamento", description="Gerencia as autorizacoes de canais para gerenciamento de mensagens.")
    @commands.has_permissions(manage_guild=True)
    async def gerenciamento(self, ctx):
        """
        Comando para configurar as autorizacoes de gerenciamento de mensagens.
        """
        embed = discord.Embed(title="Gerenciamento de Canais", description="Aqui você pode adicionar usuários para gerenciar mensagens em canais específicos.", color=discord.Color.blue())
        embed.add_field(name="Instruções:", value="1. Clique no botão 'Selecionar Canais' para escolher os canais.\n2. Clique no botão 'Adicionar Usuário' e insira o ID do usuário.\n\n**Atenção:** Somente usuários com permissão de 'Gerenciar Servidor' podem usar este comando.", inline=False)

        view = GerenciamentoView(self)
        await ctx.send(embed=embed, view=view)


    @commands.hybrid_command(name="fixar", description="Fixa uma mensagem no canal.")
    async def fixar(self, ctx, message_id: str):
        """
        Fixa uma mensagem no canal, se o usuário tiver permissão.
        """
        try:
            message_id = int(message_id)
            mensagem = await ctx.channel.fetch_message(message_id)
        except ValueError:
            await ctx.send("ID da mensagem inválido. Insira um número inteiro.")
            return
        except discord.NotFound:
            await ctx.send("Mensagem não encontrada.")
            return
        except discord.Forbidden:
            await ctx.send("Não tenho permissão para acessar essa mensagem.")
            return

        if self.tem_permissao(ctx.author.id, ctx.channel.id):
            try:
                await mensagem.pin()
                await ctx.send(f"Mensagem com ID `{message_id}` fixada com sucesso!")
            except discord.Forbidden:
                await ctx.send("Não tenho permissão para fixar mensagens neste canal.")
            except discord.HTTPException:
                await ctx.send("Erro ao fixar a mensagem.")
        else:
            await ctx.send("Você não tem permissão para fixar mensagens neste canal.")


    @commands.hybrid_command(name="desafixar", description="Desafixa uma mensagem no canal.")
    async def desafixar(self, ctx, message_id: str):
        """
        Desafixa uma mensagem no canal, se o usuário tiver permissão.
        """
        try:
            message_id = int(message_id)
            mensagem = await ctx.channel.fetch_message(message_id)
        except ValueError:
            await ctx.send("ID da mensagem inválido. Insira um número inteiro.")
            return
        except discord.NotFound:
            await ctx.send("Mensagem não encontrada.")
            return
        except discord.Forbidden:
            await ctx.send("Não tenho permissão para acessar essa mensagem.")
            return

        if self.tem_permissao(ctx.author.id, ctx.channel.id):
            try:
                await mensagem.unpin()
                await ctx.send(f"Mensagem com ID `{message_id}` desafixada com sucesso!")
            except discord.Forbidden:
                await ctx.send("Não tenho permissão para desafixar mensagens neste canal.")
            except discord.HTTPException:
                await ctx.send("Erro ao desafixar a mensagem.")
        else:
            await ctx.send("Você não tem permissão para desafixar mensagens neste canal.")


    @commands.hybrid_command(name="excluir", description="Exclui uma mensagem no canal.")
    async def excluir(self, ctx, message_id: str):
        """
        Exclui uma mensagem no canal, se o usuário tiver permissão.
        """
        try:
            message_id = int(message_id)
            mensagem = await ctx.channel.fetch_message(message_id)
        except ValueError:
            await ctx.send("ID da mensagem inválido. Insira um número inteiro.")
            return
        except discord.NotFound:
            await ctx.send("Mensagem não encontrada.")
            return
        except discord.Forbidden:
            await ctx.send("Não tenho permissão para acessar essa mensagem.")
            return

        if self.tem_permissao(ctx.author.id, ctx.channel.id):
            try:
                await mensagem.delete()
                await ctx.send(f"Mensagem com ID `{message_id}` excluída com sucesso!")
            except discord.Forbidden:
                await ctx.send("Não tenho permissão para excluir mensagens neste canal.")
            except discord.HTTPException:
                await ctx.send("Erro ao excluir a mensagem.")
        else:
            await ctx.send("Você não tem permissão para excluir mensagens neste canal.")


    def tem_permissao(self, user_id, channel_id):
        """
        Verifica se um usuário tem permissão para gerenciar mensagens em um canal.
        """
        user_id = int(user_id)
        channel_id = int(channel_id)

        if user_id in self.autorizacoes and channel_id in self.autorizacoes[user_id]:
            return True
        return False


    def adicionar_autorizacao(self, user_id, channel_ids):
        """
        Adiciona a autorização para um usuário gerenciar mensagens em um ou mais canais.
        """
        user_id = int(user_id)
        if user_id not in self.autorizacoes:
            self.autorizacoes[user_id] = []

        for channel_id in channel_ids:
            channel_id = int(channel_id)
            if channel_id not in self.autorizacoes[user_id]:
                self.autorizacoes[user_id].append(channel_id)

    def remover_autorizacao(self, user_id, channel_ids):
        """
        Remove a autorização para um usuário gerenciar mensagens em um ou mais canais.
        """
        user_id = int(user_id)
        if user_id in self.autorizacoes:
            for channel_id in channel_ids:
                channel_id = int(channel_id)
                if channel_id in self.autorizacoes[user_id]:
                    self.autorizacoes[user_id].remove(channel_id)

            if not self.autorizacoes[user_id]:
                del self.autorizacoes[user_id]


class GerenciamentoView(View):
    def __init__(self, cog: GerenciadorMensagens):
        super().__init__()
        self.cog = cog
        self.usuario_id = None  # Armazenar o ID do usuário a ser adicionado
        self.canais_selecionados = []

    @discord.ui.button(label="Selecionar Canais", style=discord.ButtonStyle.primary)
    async def selecionar_canais(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Abre um menu de seleção para o usuário escolher os canais."""
        channel_select_view = CanalSelectView(self)
        await interaction.response.send_message("Selecione os canais:", view=channel_select_view, ephemeral=True)


    @discord.ui.button(label="Adicionar Usuário", style=discord.ButtonStyle.success)
    async def adicionar_usuario(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Solicita o ID do usuário e atualiza o embed."""
        await interaction.response.send_modal(AdicionarUsuarioModal(self))


    async def atualizar_embed(self, interaction: discord.Interaction):
        """Atualiza o embed com as informações do usuário e canais adicionados."""

        embed = discord.Embed(title="Gerenciamento de Canais", description="Aqui você pode adicionar usuários para gerenciar mensagens em canais específicos.", color=discord.Color.blue())
        embed.add_field(name="Instruções:", value="1. Clique no botão 'Selecionar Canais' para escolher os canais.\n2. Clique no botão 'Adicionar Usuário' e insira o ID do usuário.\n\n**Atenção:** Somente usuários com permissão de 'Gerenciar Servidor' podem usar este comando.", inline=False)

        if self.usuario_id:
            canais_mencionados = ", ".join([f"<#{canal_id}>" for canal_id in self.canais_selecionados]) if self.canais_selecionados else "Nenhum canal selecionado"
            embed.add_field(name="Usuário Adicionado:", value=f"<@{self.usuario_id}> adicionado como gerenciador dos canais: {canais_mencionados}", inline=False)


        await interaction.response.edit_message(embed=embed, view=self)

class CanalSelect(Select):
    def __init__(self, gerenciamento_view: GerenciamentoView, options):
        self.gerenciamento_view = gerenciamento_view
        super().__init__(placeholder="Selecione os canais...", min_values=1, max_values=len(options), options=options)

    async def callback(self, interaction: discord.Interaction):
        self.gerenciamento_view.canais_selecionados.extend([int(channel_id) for channel_id in self.values])
        await interaction.response.send_message(f"Canais selecionados: {', '.join([f'<#{channel_id}>' for channel_id in self.values])}", ephemeral=True)


class CanalSelectView(View):
    def __init__(self, gerenciamento_view: GerenciamentoView):
        super().__init__()
        self.gerenciamento_view = gerenciamento_view
        channels = [channel for channel in gerenciamento_view.cog.bot.get_all_channels() if isinstance(channel, discord.TextChannel)]
        options = [discord.SelectOption(label=channel.name, value=str(channel.id), description=f"Canal: {channel.name}") for channel in channels]

        # Discord limita Select menus a 25 opções e 5 componentes por view.
        for i in range(0, len(options), 25):
            select = CanalSelect(gerenciamento_view, options[i:i+25])
            self.add_item(select)
            if len(self.children) >= 5:  # Limite de componentes por view
                break



class AdicionarUsuarioModal(discord.ui.Modal, title='Adicionar Usuário'):
    def __init__(self, gerenciamento_view: GerenciamentoView):
        super().__init__()
        self.gerenciamento_view = gerenciamento_view

    usuario_id = discord.ui.TextInput(label="ID do Usuário", placeholder="Insira o ID do usuário a ser adicionado")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.usuario_id.value)
        except ValueError:
            await interaction.response.send_message("ID de usuário inválido. Insira um número inteiro.", ephemeral=True)
            return

        self.gerenciamento_view.usuario_id = user_id
        self.gerenciamento_view.cog.adicionar_autorizacao(user_id, self.gerenciamento_view.canais_selecionados)
        await self.gerenciamento_view.atualizar_embed(interaction)


async def setup(bot):
    await bot.add_cog(GerenciadorMensagens(bot))