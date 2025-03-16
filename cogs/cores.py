import discord
from discord import app_commands
from discord.ext import commands

class CoresInteract(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

        # Lista de cores pastel (você pode ajustar as cores conforme sua preferência)
        self.cores_pastel = [
            0xF5F5DC,  # Ivory
            0xF0FFF0,  # Snow
            0xE0FFFF,  # Lightcyan
            0xFFE4C4,  # Lightgoldenrodyellow
            0xFFF5EE,  # Lavenderblush
            0xFAEBD7,  # AntiqueWhite
            0x90EE90,  # Lightgreen
            0xADD8E6,  # Lightblue
            0x7FFFD4,  # Aquamarine
            0xF08080,  # Lightcoral
            0xFFFFE0,  # Lightyellow
            0x98FB98,  # Palegreen
            0xD8BFD8,  # Thistle
            0xFFDAB9,  # Peachpuff
            0xFFFAF0  #  FloralWhite
        ]

        # Define o cargo de referência (ID do cargo do seu servidor)
        self.cargo_alvo_id = 1302640393581756508  # Substitua pelo ID do cargo de referência

    @app_commands.command(name="cor", description="Cria ou modifica um cargo com a cor desejada.")
    @app_commands.describe(
        numero="Número da cor (1-15) da lista de cores pastel (opcional).",
        hex="Código hexadecimal da cor desejada (opcional).",
        nome="Nome do cargo (opcional). Pode ser um emoji unicode."
    )
    async def cor(self, interaction: discord.Interaction, numero: int = None, hex: str = None, nome: str = None):
        """Cria ou modifica um cargo com a cor desejada.

        **Parâmetros:**
        - `numero`: Número da cor (1-15) da lista de cores pastel (opcional).
        - `hex`: Código hexadecimal da cor desejada (opcional).
        - `nome`: Nome do cargo (opcional). Pode ser um emoji unicode.

        **Exemplo:**
        - `/cor numero 5` - Cria/modifica um cargo com a cor número 5 da lista.
        - `/cor hex #FF0000` - Cria/modifica um cargo com a cor vermelha (#FF0000).
        - `/cor nome 🐶` - Cria/modifica um cargo com o nome "🐶".
        """
        # Verificando a cor
        cor = None
        if numero is not None:
            if 1 <= numero <= 15:
                cor = self.cores_pastel[numero - 1]
            else:
                await interaction.response.send_message(f"Número inválido. Por favor, escolha um número entre 1 e 15.")
                return
        elif hex is not None:
            try:
                cor = int(hex.lstrip("#"), 16)
            except ValueError:
                await interaction.response.send_message(f"Código hexadecimal inválido. Por favor, insira um código válido.")
                return
        else:
            await interaction.response.send_message(f"Você precisa fornecer um número da lista de cores pastel ou um código hexadecimal.")
            return

        # Definindo o nome do cargo (emoji)
        emoji = nome if nome else "⚡"  #  "⚡" é o nome padrão, substitua pelo seu emoji desejado

        # Obtendo o cargo de referência
        cargo_alvo = interaction.guild.get_role(self.cargo_alvo_id)
        if not cargo_alvo:
            await interaction.response.send_message(f"O cargo de referência com ID {self.cargo_alvo_id} não foi encontrado. Verifique se o ID está correto.")
            return

        # Procurando por um cargo existente com o emoji como nome
        cargo = None
        for role in interaction.guild.roles:
            if role.name == emoji:
                cargo = role
                break

        # Criando o cargo se não existir
        if cargo is None:
            try:
                cargo = await interaction.guild.create_role(
                    name=emoji,
                    colour=discord.Colour(cor),
                    hoist=True,
                    reason="Criado pelo comando /cor"
                )

                # Move o cargo para a posição imediatamente abaixo do cargo_alvo
                pos = cargo_alvo.position + 1
                await cargo.edit(position=pos)

            except discord.HTTPException as e:
                await interaction.response.send_message(f"Erro ao criar o cargo: {e}")
                return

        # Atualizando a cor e o nome do cargo
        if cor is not None:
            await cargo.edit(colour=discord.Colour(cor))
        if nome is not None:
            await cargo.edit(name=emoji)

        # Adicionando o cargo ao usuário (se ele ainda não o tiver)
        if cargo not in interaction.user.roles:
            await interaction.user.add_roles(cargo)

        await interaction.response.send_message(f"Cargo criado/modificado com sucesso! 🎉")

    

async def setup(bot):
    await bot.add_cog(CoresInteract(bot))