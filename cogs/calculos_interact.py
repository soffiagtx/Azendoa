import discord
from discord import app_commands
from discord.ext import commands
from sympy import *
import locale 
from locale import format_string

locale.setlocale(locale.LC_ALL, 'pt_Br')

class CálculosInteract(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    def formatar_expressão(self, expressão):
        expressão_sem_espaço =  expressão.replace(" ", "")
        expressão_com_ponto = expressão_sem_espaço.replace(",", ".")
        return expressão_com_ponto
    
    @app_commands.command(description='Calcula o resultado de uma expressão')
    @app_commands.describe(expressão='Digite a expressão')
    async def calcular(self, interact: discord.Interaction, expressão:str):
        try:
            expressão_formatada = self.formatar_expressão(expressão)
            resultado = sympify(expressão_formatada).evalf()
            if resultado % 2 == 0:
                resultado_formatado = locale.format_string("%d", resultado, grouping=True)
            else:
                resultado_formatado = locale.format_string("%.2f", resultado, grouping=True)
            await interact.response.send_message(f"{expressão} = {resultado_formatado}", ephemeral=True)
        except SympifyError:
            await interact.response.send_message("Erro no conteúdo digitado da expressão.", ephemeral=True)
        except TypeError:
            await interact.response.send_message("Erro no tipo de dado da expressão.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CálculosInteract(bot))