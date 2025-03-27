import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio

class CriadorPastas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="criar_canais", description="Cria canais de texto com base nas pastas em /temas.")
    @app_commands.describe(categoria="ID da categoria inicial onde os canais serão criados.")
    async def criar_canais(self, interaction: discord.Interaction, categoria: str):
        """
        Cria canais de texto em uma categoria, baseados nos nomes das pastas dentro da pasta "temas".
        Cria novas categorias se o limite da categoria inicial for atingido.
        """
        await interaction.response.defer()  # Responde imediatamente para evitar timeout

        try:
            categoria_id = int(categoria)
            current_category = self.bot.get_channel(categoria_id)

            if not isinstance(current_category, discord.CategoryChannel):
                await interaction.followup.send("ID inválido.  A categoria informada não foi encontrada ou não é uma categoria válida.", ephemeral=True)
                return

            pasta_temas = os.path.join(os.path.dirname(__file__), "temas")  # Nome da pasta onde estão as pastas de temas.  Relative to the cog's location.

            if not os.path.exists(pasta_temas):
                await interaction.followup.send(f"A pasta '{pasta_temas}' não foi encontrada no diretório do bot.", ephemeral=True)
                return

            temas = [d for d in os.listdir(pasta_temas) if os.path.isdir(os.path.join(pasta_temas, d))]  # Obtém nomes das pastas dentro de "temas"
            temas_a_criar = temas.copy() #Copia a lista de temas para sabermos o progresso e o que ainda tem que ser criado

            canais_criados = []
            
            async def criar_canais_na_categoria(category, temas_para_criar):
                nonlocal canais_criados
                canais_existentes = {channel.name for channel in category.text_channels} # Obtém os nomes dos canais de texto existentes na categoria

                for tema in list(temas_para_criar): #Iterar sobre uma cópia da lista para poder remover elementos dela
                    nome_canal = tema.lower()  # Converte para minúsculo para nome do canal
                    nome_canal_formatado = f"📂│{nome_canal}"
                    
                    if nome_canal in canais_existentes or nome_canal_formatado in canais_existentes: # Verifica se o canal já existe (nome original ou formatado)
                        print(f"Canal '{nome_canal_formatado}' já existe na categoria. Pulando...") #opcional log no console
                        temas_para_criar.remove(tema)
                        continue #pula para a proxima iteração

                    try:
                        await category.create_text_channel(nome_canal_formatado)
                        canais_criados.append(nome_canal_formatado)
                        temas_para_criar.remove(tema)
                        await asyncio.sleep(1)  # Delay para evitar rate limits (opcional, mas recomendado)

                    except discord.Forbidden:
                        await interaction.followup.send(f"Não tenho permissão para criar canais na categoria {category.name}.", ephemeral=True)
                        return False #Indica que não foi possível continuar a criar canais nesta categoria
                    except discord.HTTPException as e:
                        if e.status == 400 and "Maximum number of channels in category reached" in e.text:
                            #Categoria cheia, retornar para criar outra
                            return False
                        else:
                            await interaction.followup.send(f"Erro ao criar o canal {nome_canal_formatado}: {e}", ephemeral=True)
                            return False

                return True #Indica que criou todos os canais com sucesso

            guild = current_category.guild
            
            while temas_a_criar: #Enquanto ainda tiver temas para criar
                sucesso = await criar_canais_na_categoria(current_category, temas_a_criar) #Tenta criar na categoria atual
                if not sucesso and temas_a_criar:  # Categoria está cheia ou houve um erro
                    # Criar nova categoria
                    try:
                        current_category = await guild.create_category("🎲 ‧ Imagens")
                        print(f"Nova categoria criada: {current_category.name} ({current_category.id})") #Log para debug

                    except discord.Forbidden:
                        await interaction.followup.send("Não tenho permissão para criar novas categorias.", ephemeral=True)
                        break #Para o loop se não conseguir criar categoria
                    except discord.HTTPException as e:
                         await interaction.followup.send(f"Erro ao criar nova categoria: {e}", ephemeral=True)
                         break

            if canais_criados:
                canais_str = "\n".join(canais_criados)
                await interaction.followup.send(f"Canais criados com sucesso:\n{canais_str}")
            else:
                await interaction.followup.send("Nenhum canal foi criado.")


        except ValueError:
            await interaction.followup.send("O ID da categoria deve ser um número inteiro.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Ocorreu um erro inesperado: {e}", ephemeral=True)
            print(f"Erro no comando criar_canais: {e}")  # Para log no console



async def setup(bot):
    await bot.add_cog(CriadorPastas(bot))