import discord
from discord.ext import commands
from sympy import *
import locale
from locale import format_string

class Cálculos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    def formatar_expressão(self, expressão):
        expressão_sem_espaco = expressão.replace(" ", "")
        expressão_com_ponto = expressão_sem_espaco.replace(",", ".")
        return expressão_com_ponto

    @commands.command()
    async def calcular(self, ctx:commands.Context, *, expressão: str):
        try:    
            expressão_formatada = self.formatar_expressão(expressão)
            resultado = sympify(expressão_formatada).evalf()
            if resultado % 2 == 0:
                resultado_formatado = locale.format_string("%d", resultado, grouping=True)
            else:
                resultado_formatado = locale.format_string("%.2f", resultado, grouping=True)
            await ctx.reply(f"{expressão} = {resultado_formatado}")
        except SympifyError:
            await ctx.reply("Erro na sintaxe da expressão.")
        except TypeError:
            await ctx.reply("Erro no tipo de dado da expressão. ")

    @commands.command()
    async def calc(self, ctx: commands.Context, *, expressão: str):
        comando_calcular = self.bot.get_command("calcular")
        await comando_calcular(ctx, expressão=expressão)

    @commands.command()
    async def c(self, ctx:commands.Context, *, expressão: str):
        comando_calcular = self.bot.get_command("calcular")
        await comando_calcular(ctx, expressão=expressão)
        
async def setup(bot):
    await bot.add_cog(Cálculos(bot))