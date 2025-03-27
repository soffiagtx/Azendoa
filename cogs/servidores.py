import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord.ui import Button, View


class Servidores(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.servidor_escolhido = None
        super().__init__()

    @commands.command(name="servidores", aliases=["servers"])
    async def servidores(self, ctx: Context):
        """
        Mostra uma lista de servidores onde o bot está.
        """
        guilds = list(self.bot.guilds)
        total_guilds = len(guilds)
        per_page = 20
        total_pages = (total_guilds + per_page - 1) // per_page  # Calculate total pages

        current_page = 1

        async def create_embed(page: int):
            start_index = (page - 1) * per_page
            end_index = min(page * per_page, total_guilds)

            embed = discord.Embed(
                title=f"Servidores ({page}/{total_pages})",
                description=f"O bot está em {total_guilds} servidores.",
                color=discord.Color.blue(),
            )

            for i in range(start_index, end_index):
                guild = guilds[i]
                embed.add_field(
                    name=guild.name,
                    value=f"Dono: {guild.owner.mention}\nID: {guild.id}",
                    inline=False,
                )

            embed.set_footer(text=f"Página {page}/{total_pages}")
            return embed

        async def update_message(page: int, message: discord.Message = None):
            embed = await create_embed(page)
            if message:
                await message.edit(embed=embed, view=view)
            else:
                return await ctx.send(embed=embed, view=view)


        async def next_callback(interaction: discord.Interaction):
            nonlocal current_page
            if interaction.user != ctx.author:
                await interaction.response.send_message("Você não pode interagir com este botão.", ephemeral=True)
                return

            if current_page < total_pages:
                current_page += 1
                await update_message(current_page, interaction.message)
                await interaction.response.defer()
            else:
                 await interaction.response.send_message("Você já está na última página.", ephemeral=True)


        async def prev_callback(interaction: discord.Interaction):
            nonlocal current_page
            if interaction.user != ctx.author:
                await interaction.response.send_message("Você não pode interagir com este botão.", ephemeral=True)
                return
            if current_page > 1:
                current_page -= 1
                await update_message(current_page, interaction.message)
                await interaction.response.defer()
            else:
                await interaction.response.send_message("Você já está na primeira página.", ephemeral=True)


        if total_pages > 1:
            next_button = Button(label="Próxima", style=discord.ButtonStyle.primary)
            prev_button = Button(label="Anterior", style=discord.ButtonStyle.primary)
            next_button.callback = next_callback
            prev_button.callback = prev_callback

            view = View(timeout=60)
            view.add_item(prev_button)
            view.add_item(next_button)

            await update_message(current_page)
        else:
            view = None
            embed = await create_embed(current_page)
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Servidores(bot))