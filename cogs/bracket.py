import discord
from discord import app_commands
from discord.ext import commands
import random

class Bracket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

   # @app_commands.command(description='Monte seu Bracket')
   # @app_coomands.descr



async def setup(bot):
    await bot.add_cog(Bracket(bot))
