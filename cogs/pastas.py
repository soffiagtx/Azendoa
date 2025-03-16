import discord
from discord import app_commands
from discord.ext import commands
import random
from PIL import Image, ImageDraw, ImageFont
import asyncio
from datetime import datetime, timedelta
import re
import os
import requests
from io import BytesIO
from requests.exceptions import ConnectTimeout, ReadTimeout
import json
import unicodedata

class TemasInteract(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        self.temas_pasta = os.path.join(os.path.dirname(__file__), "temas")
        self.modified_names_file = os.path.join(self.temas_pasta, "modified_names.json")
        self.completed_themes_file = os.path.join(self.temas_pasta, "completed_themes.json")
        self.modified_names = self.load_modified_names()
        self.completed_themes = self.load_completed_themes()
        self.processing_editor = set()
        self.processing_aprender = set()
        self.processing_listar = set()
        self.create_json_if_not_exists()

    def create_json_if_not_exists(self):
        # Verifica se o diretório 'temas' existe, se não, cria o diretório
        if not os.path.exists(self.temas_pasta):
            print(f"Criando diretório 'temas' em: {self.temas_pasta}")
            os.makedirs(self.temas_pasta)

        # Verifica se o arquivo 'modified_names.json' existe, se não, cria o arquivo
        if not os.path.exists(self.modified_names_file):
            print(f"Criando arquivo JSON em: {self.modified_names_file}")
            self.save_modified_names()

        # Verifica se o arquivo 'completed_themes.json' existe, se não, cria o arquivo
        if not os.path.exists(self.completed_themes_file):
            print(f"Criando arquivo JSON em: {self.completed_themes_file}")
            self.save_completed_themes()

    def load_modified_names(self):
        # Carrega o conteúdo do arquivo 'modified_names.json'
        if os.path.exists(self.modified_names_file):
            with open(self.modified_names_file, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    # Normaliza os dados se necessário
                    normalized_data = {self.normalize_text(key): self.normalize_text(value) for key, value in data.items()}
                    return normalized_data
                except json.JSONDecodeError:
                    print("Erro ao decodificar o arquivo JSON, criando um novo dicionário.")
                    return {}
        return {}  # Se o arquivo não existir, retorna um dicionário vazio

    def load_completed_themes(self):
        # Carrega o conteúdo do arquivo 'completed_themes.json'
        if os.path.exists(self.completed_themes_file):
            with open(self.completed_themes_file, 'r', encoding='utf-8') as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    print("Erro ao decodificar o arquivo JSON para temas completos, criando um novo dicionário.")
                    return {}
        return {}  # Se o arquivo não existir, retorna um dicionário vazio

    def save_modified_names(self):
        # Salva os dados no arquivo 'modified_names.json' com encoding UTF-8
        with open(self.modified_names_file, 'w', encoding='utf-8') as file:
            json.dump(self.modified_names, file, indent=4, ensure_ascii=False)

    def save_completed_themes(self):
        # Salva os dados no arquivo 'completed_themes.json' com encoding UTF-8
        with open(self.completed_themes_file, 'w', encoding='utf-8') as file:
            json.dump(self.completed_themes, file, indent=4, ensure_ascii=False)


    def normalize_text(self, text):
        return unicodedata.normalize('NFC', text)

    @commands.command(name="listar")
    async def listar(self, ctx: commands.Context):
       if ctx.author.id in self.processing_listar:
            await ctx.send("Você já está usando o listar. Use `listarfim` para finalizar o processo atual.")
            return
       self.processing_listar.add(ctx.author.id)
       message = await ctx.send("Verificando lista... Aguarde.")

       def check_bot_message(m):
            return m.author.id == 628120853154103316 and len(m.embeds) > 0 and \
                   "Lista de" in (m.embeds[0].description or "") and "em ordem alfabética!" in (
                           m.embeds[0].description or "")

       try:
            async with ctx.typing():
                async for msg in ctx.channel.history(limit=5):
                    if check_bot_message(msg):
                        bot_message = msg
                        break
                else:
                    await ctx.send("Não encontrei uma mensagem do bot com a lista.")
                    self.processing_listar.discard(ctx.author.id)
                    return

                await self.processar_listar(ctx, bot_message, message, ctx.author.id)
       except asyncio.TimeoutError:
            await ctx.send("Tempo limite excedido ao esperar a mudança de página.")
       except Exception as e:
            await ctx.send(f"Ocorreu um erro: {e}")
       finally:
           self.processing_listar.discard(ctx.author.id)
    
    @commands.command(name="listarfim")
    async def listar_fim(self, ctx: commands.Context):
        if ctx.author.id in self.processing_listar:
            self.processing_listar.discard(ctx.author.id)
            await ctx.send("Processo de listagem do tema finalizado.")
        else:
            await ctx.send("Você não está em nenhum processo de listagem de tema.")

    async def processar_listar(self, ctx, bot_message, message, user_id):
       all_items = []
       current_page = 1
       total_pages = 0
       
       try:
            while True:
                if user_id not in self.processing_listar:
                    await message.edit(content="Processo de listagem interrompido")
                    return
                embed = bot_message.embeds[0]
                footer_text = embed.footer.text

                match = re.search(r"Página (\d+) de (\d+)", footer_text)
                if match:
                    current_page = int(match.group(1))
                    total_pages = int(match.group(2))

                    for field in embed.fields:
                            value = field.value.strip()
                            if value.startswith("```fix") and value.endswith("```"):
                                value = value[6:-3].strip()
                            all_items.extend([item.strip() for item in value.split('\n') if item.strip()])

                    if current_page == total_pages:
                         break

                    next_page = current_page + 1
                    await message.edit(content=f"Verificando lista... Aguarde.\nMude para a página {next_page}")
                    
                    while True:
                        if user_id not in self.processing_listar:
                           await message.edit(content="Processo de listagem interrompido")
                           return
                        try:
                            new_message = await ctx.channel.fetch_message(bot_message.id)
                            if new_message.embeds[0].footer.text != footer_text:
                                bot_message = new_message
                                break
                            await asyncio.sleep(1)
                        except Exception as e:
                            print(f"Erro ao buscar nova mensagem: {e}")
                            await asyncio.sleep(1)
                            continue
                else:
                    await ctx.send("Não consegui extrair informações de página do rodapé.")
                    break
            
            tema = re.search(r"Lista de (.+?) em ordem alfabética!", embed.description or embed.title).group(1)
            tema_limpo = tema.strip('`').strip()
            pasta_temas = os.path.join(os.path.dirname(__file__), "temas")
            caminho_tema = os.path.join(pasta_temas, tema_limpo)
            nome_arquivo = f"lista_{tema_limpo.lower().replace(' ', '_')}.txt"
            caminho_completo = os.path.join(caminho_tema, nome_arquivo)

            os.makedirs(caminho_tema, exist_ok=True)

            with open(caminho_completo, "w", encoding="utf-8") as f:
                 f.write("\n".join(all_items))

            await message.edit(content=f"Lista salva com sucesso em {tema_limpo}")
        
       except Exception as e:
          await ctx.send(f"Ocorreu um erro: {e}")

    @commands.command(name="aprender")
    async def aprender_tema(self, ctx: commands.Context, tema: str):
        if ctx.author.id in self.processing_aprender:
            await ctx.send("Você já está aprendendo um tema. Use `.aprenderfim` para finalizar o processo atual.")
            return

        self.processing_aprender.add(ctx.author.id)

        try:
            caminho_tema = os.path.join(self.temas_pasta, tema)
            nome_arquivo = f"lista_{tema.lower().replace(' ', '_')}.txt"
            caminho_completo = os.path.join(caminho_tema, nome_arquivo)

            if not os.path.exists(caminho_completo):
                await ctx.send(f"Não encontrei a lista para o tema '{tema}'.")
                return

            with open(caminho_completo, "r", encoding="utf-8") as f:
                lista_itens = [self.normalize_text(item.strip().lower()) for item in f.readlines()]

            imagens_pasta = os.path.join(self.temas_pasta, tema)
            if not os.path.exists(imagens_pasta) or not os.listdir(imagens_pasta):
                await ctx.send(f"Não encontrei imagens para o tema '{tema}'.")
                return
            nomes_imagens = [f for f in os.listdir(imagens_pasta) if f.lower().endswith(('.jpg', '.png'))]

            nomes_imagens_tratados = []
            for nome_imagem in nomes_imagens:
                nome_sem_extensao = os.path.splitext(nome_imagem)[0]
                nome_sem_mod = nome_sem_extensao.replace("mod ", "")

                if nome_sem_mod in self.modified_names:
                    nome_original = self.modified_names[nome_sem_mod]
                    nome_final = nome_original.replace(f"{tema} ", "").lower()
                    nomes_imagens_tratados.append(self.normalize_text(nome_final))
                else:
                    nome_final = nome_sem_mod.replace(f"{tema} ", "").lower()
                    nomes_imagens_tratados.append(self.normalize_text(nome_final))

            faltantes = [item for item in lista_itens if item not in nomes_imagens_tratados]

            if not faltantes:
                await ctx.send("Você já aprendeu todas as palavras deste tema!")
                self.processing_aprender.discard(ctx.author.id)
                return

            await self.processar_tema(ctx, tema, faltantes, ctx.author.id)

        except Exception as e:
            await ctx.send(f"Ocorreu um erro: {e}")
        finally:
            # Garante que o ID do usuário seja removido, mesmo em caso de erro
            if ctx.author.id in self.processing_aprender:
                self.processing_aprender.discard(ctx.author.id)

    async def aprenderfim(self, ctx: commands.Context):
        # Remove o ID do usuário se estiver no set, independentemente do estado do processo
        if ctx.author.id in self.processing_aprender:
            self.processing_aprender.discard(ctx.author.id)
            await ctx.send("Processo de aprendizado do tema finalizado.")
        else:
            await ctx.send("Você não está em nenhum processo de aprendizado de tema.")
            
    async def processar_tema(self, ctx, tema, lista_itens, user_id):
        try:
            for i, item in enumerate(lista_itens):
                if user_id not in self.processing_aprender:
                    await ctx.send("Processo de aprendizado interrompido.")
                    return

                embed = discord.Embed(title=f"Aprendendo tema: {tema} - Item: {item}", color=discord.Color.blue())
                embed.add_field(name="Utilize o comando abaixo:", value=f"```.ver {tema} {item}```", inline=False)
                await ctx.send(embed=embed)

                try:
                    await self.baixar_imagens_individual(ctx, tema, item, user_id)
                except Exception as e:
                    await ctx.send(f"Erro ao processar '{item}': {e}")

        finally:
            # Garante que o ID do usuário seja removido ao final do processo, mesmo que interrompido
            if ctx.author.id in self.processing_aprender:
                self.processing_aprender.discard(ctx.author.id)

    async def baixar_imagens_individual(self, ctx, tema, item, user_id):
        def check(msg):
            return msg.author.id == 628120853154103316 and msg.channel.id == ctx.channel.id and len(msg.embeds) > 0

        max_retries = 3
        retry_delay = 5
        try:
            resposta_bot = await asyncio.wait_for(self.bot.wait_for('message', check=check), timeout=300)  # 5 minutos
        except asyncio.TimeoutError:
            await ctx.send("Tempo limite de 5 minutos excedido. Processo de aprendizado interrompido.")
            if user_id in self.processing_aprender:
                self.processing_aprender.discard(user_id)
            return

        for attempt in range(max_retries):
            if user_id not in self.processing_aprender:
                return
            try:
                embed = resposta_bot.embeds[0]
                if embed and embed.image and item.lower() in (embed.description or "").lower():
                    image_url = embed.image.url
                    response = requests.get(image_url, stream=True, timeout=10)
                    response.raise_for_status()
                    image = Image.open(BytesIO(response.content))

                    original_name = f"{tema} {item.replace(' ', ' ')}"
                    safe_name = self.safe_filename(original_name)

                    if safe_name != original_name:
                        nome_arquivo_imagem = f"mod {safe_name}"
                        self.modified_names[nome_arquivo_imagem] = original_name
                        self.save_modified_names()
                    else:
                        nome_arquivo_imagem = safe_name

                    caminho_imagem = os.path.join(self.temas_pasta, tema,
                                                   f"{nome_arquivo_imagem}.{'png' if image.mode == 'RGBA' else 'jpg'}")

                    if image.mode == 'P':
                        image = image.convert('RGB')
                    image.save(caminho_imagem)

                    usuario_inicial = ctx.author
                    embedo = discord.Embed(title='Download Concluído!', description='Imagem salva com sucesso!')
                    embedo.set_author(name=f'{usuario_inicial.name}', icon_url=f'{usuario_inicial.display_avatar}')
                    embedo.color = usuario_inicial.color
                    embedo.add_field(name='Nome:', value=nome_arquivo_imagem)
                    embedo.set_image(url=image_url)
                    await ctx.send(embed=embedo)
                    return
                else:
                    await ctx.send(f"Não foi encontrada imagem para o item '{item}'.")
                    return

            except (ConnectTimeout, ReadTimeout, requests.exceptions.RequestException) as e:
                print(f"Erro ao baixar imagem para '{item}' (Tentativa {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    await ctx.send(f"Falha ao baixar imagem para '{item}' após várias tentativas.")
                    return
            except Exception as e:
                await ctx.send(f"Ocorreu um erro: {e}")
                return

    def safe_filename(self, filename):
        invalid_chars = r'[:/\\<>|"\'?*#]'
        return re.sub(invalid_chars, '_', filename)
                
    @commands.command(name="editor")
    async def editor_tema(self, ctx: commands.Context, tema: str):
        if ctx.author.id in self.processing_editor:
            await ctx.send("Você já está usando o editor. Use `editorfim` para finalizar o processo atual.")
            return
        self.processing_editor.add(ctx.author.id)
        
        caminho_tema = os.path.join(self.temas_pasta, tema)
        nome_arquivo = f"lista_{tema.lower().replace(' ', '_')}.txt"
        caminho_completo = os.path.join(caminho_tema, nome_arquivo)

        if not os.path.exists(caminho_completo):
            await ctx.send(f"Não encontrei a lista para o tema '{tema}'.")
            self.processing_editor.discard(ctx.author.id)
            return

        try:
            with open(caminho_completo, "r", encoding="utf-8") as f:
                lista_itens = [item.strip().lower() for item in f.readlines()]
            
            await self.processar_editor(ctx, tema, lista_itens, ctx.author.id)
        except Exception as e:
            await ctx.send(f"Ocorreu um erro: {e}")
        finally:
             if ctx.author.id in self.processing_editor:
                self.processing_editor.discard(ctx.author.id)

    @commands.command(name="editorfim")
    async def editor_fim(self, ctx: commands.Context):
        if ctx.author.id in self.processing_editor:
            self.processing_editor.discard(ctx.author.id)
            await ctx.send("Processo de edição do tema finalizado.")
        else:
            await ctx.send("Você não está em nenhum processo de edição de tema.")
            
    async def processar_editor(self, ctx, tema:str, lista_itens, user_id):
        message = await ctx.send("Procurando mensagem do bot com editor... Aguarde.")

        def check_bot_message(m):
            return m.author.id == 628120853154103316 and len(m.embeds) > 0 and \
                   "Navegação de editor." in (m.embeds[0].footer.text or "")

        try:
            async with ctx.typing():
                async for msg in ctx.channel.history(limit=5):
                    if check_bot_message(msg):
                        bot_message = msg
                        break
                else:
                    await ctx.send("Não encontrei uma mensagem do bot com editor.")
                    return
                await self.baixar_imagens_editor(ctx, tema, bot_message, message, user_id)

        except Exception as e:
            await ctx.send(f"Ocorreu um erro: {e}")

    async def baixar_imagens_editor(self, ctx, tema, bot_message, message, user_id):
        current_page = 1
        total_pages = 0
        try:
            bot_message = await asyncio.wait_for(ctx.channel.fetch_message(bot_message.id), timeout=300) #5min
        except asyncio.TimeoutError:
            await ctx.send("Tempo limite de 5 minutos excedido. Processo de edição interrompido.")
            if user_id in self.processing_editor:
                self.processing_editor.discard(user_id)
            return
        
        try:
            while True:
                if user_id not in self.processing_editor:
                    await message.edit(content="Processo de edição interrompido")
                    return

                embed = bot_message.embeds[0]
                footer_text = embed.footer.text
                print(f"Footer text: {footer_text}")
                print(f"Conteúdo do embed: {embed.to_dict()}") # Adicionado o print do embed

                match = re.search(r"Imagem (\d+) de (\d+)", footer_text)
                if match:
                    current_page = int(match.group(1))
                    total_pages = int(match.group(2))

                    image_name = None
                    if embed.description:
                        match_name = re.search(r"```markdown\s*#(.+?)```", embed.description, re.DOTALL)
                        if match_name:
                            image_name = match_name.group(1).strip()

                    if image_name:
                        
                        if embed.image:
                            image_url = embed.image.url
                            
                            max_retries = 3
                            retry_delay = 5
                            for attempt in range(max_retries):
                                if user_id not in self.processing_editor:
                                    await message.edit(content="Processo de edição interrompido")
                                    return
                                try:
                                    response = requests.get(image_url, stream=True, timeout=10)
                                    response.raise_for_status()
                                    image = Image.open(BytesIO(response.content))
                                    
                                    original_name = f"{tema} {image_name.replace(' ', ' ')}"
                                    safe_name = self.safe_filename(original_name)
                                    
                                    if safe_name != original_name:
                                        nome_arquivo_imagem = f"mod {safe_name}"
                                        self.modified_names[nome_arquivo_imagem] = original_name
                                        self.save_modified_names()
                                    else:
                                        nome_arquivo_imagem = safe_name
                                        
                                    caminho_imagem = os.path.join(self.temas_pasta, tema,
                                                    f"{nome_arquivo_imagem}.{'png' if image.mode == 'RGBA' else 'jpg'}")
                                    
                                    if image.mode == 'P':
                                        image = image.convert('RGB')
                                    image.save(caminho_imagem)

                                    embedo = discord.Embed(title='Download Concluído!', description='Imagem salva com sucesso!')
                                    embedo.set_author(name=f'{ctx.author.name}', icon_url=f'{ctx.author.display_avatar}')
                                    embedo.color = ctx.author.color if hasattr(ctx.author, 'color') else discord.Color.default()
                                    embedo.add_field(name='Nome:', value=nome_arquivo_imagem)
                                    embedo.set_image(url=image_url)
                                    await message.edit(embed=embedo)
                                    break
                                except (ConnectTimeout, ReadTimeout, requests.exceptions.RequestException) as e:
                                    print(f"Erro ao baixar imagem para '{image_name}' (Tentativa {attempt+1}/{max_retries}): {e}")
                                    if attempt < max_retries - 1:
                                        await asyncio.sleep(retry_delay)
                                    else:
                                        await ctx.send(f" Falha ao baixar imagem para '{image_name}' após várias tentativas.")
                                        break
                        else:
                           await message.edit(content="Não foi encontrada imagem no embed.")
                                
                        if current_page == total_pages:
                           await message.edit(content=f"Todas as imagens do tema: '{tema}' foram baixadas")
                           break

                        next_page = current_page + 1
                        await message.edit(content=f"### Imagem _{image_name}_ salva com sucesso. \n# Mude para a página {next_page}")
                        while True:
                            if user_id not in self.processing_editor:
                                await message.edit(content="Processo de edição interrompido")
                                return
                            try:
                                new_message = await ctx.channel.fetch_message(bot_message.id)
                                if new_message.embeds[0].footer.text != footer_text:
                                    bot_message = new_message
                                    break
                                await asyncio.sleep(1)
                            except Exception as e:
                                print(f"Erro ao buscar nova mensagem: {e}")
                                await asyncio.sleep(1)
                                continue
                    else:
                         await ctx.send("Não consegui encontrar nome da imagem.")
                         break

                else:
                    image_name = None
                    if embed.description:
                        match_name = re.search(r"```markdown\s*#(.+?)```", embed.description, re.DOTALL)
                        if match_name:
                            image_name = match_name.group(1).strip()
                    if image_name:
                        if embed.image:
                            image_url = embed.image.url
                            
                            max_retries = 3
                            retry_delay = 5
                            for attempt in range(max_retries):
                                if user_id not in self.processing_editor:
                                    await message.edit(content="Processo de edição interrompido")
                                    return
                                try:
                                    response = requests.get(image_url, stream=True, timeout=10)
                                    response.raise_for_status()
                                    image = Image.open(BytesIO(response.content))
                                    
                                    original_name = f"{tema} {image_name.replace(' ', ' ')}"
                                    safe_name = self.safe_filename(original_name)
                                    
                                    if safe_name != original_name:
                                        nome_arquivo_imagem = f"mod {safe_name}"
                                        self.modified_names[nome_arquivo_imagem] = original_name
                                        self.save_modified_names()
                                    else:
                                        nome_arquivo_imagem = safe_name
                                        
                                    caminho_imagem = os.path.join(self.temas_pasta, tema,
                                                    f"{nome_arquivo_imagem}.{'png' if image.mode == 'RGBA' else 'jpg'}")
                                    
                                    if image.mode == 'P':
                                        image = image.convert('RGB')
                                    image.save(caminho_imagem)

                                    embedo = discord.Embed(title='Download Concluído!', description='Imagem salva com sucesso!')
                                    embedo.set_author(name=f'{ctx.author.name}', icon_url=f'{ctx.author.display_avatar}')
                                    embedo.color = ctx.author.color if hasattr(ctx.author, 'color') else discord.Color.default()
                                    embedo.add_field(name='Nome:', value=nome_arquivo_imagem)
                                    embedo.set_image(url=image_url)
                                    await message.edit(embed=embedo)
                                    break
                                except (ConnectTimeout, ReadTimeout, requests.exceptions.RequestException) as e:
                                    print(f"Erro ao baixar imagem para '{image_name}' (Tentativa {attempt+1}/{max_retries}): {e}")
                                    if attempt < max_retries - 1:
                                        await asyncio.sleep(retry_delay)
                                    else:
                                        await ctx.send(f" Falha ao baixar imagem para '{image_name}' após várias tentativas.")
                                        break
                        else:
                            await message.edit(content="Não foi encontrada imagem no embed.")
                    else:
                        await message.edit("Não foi encontrado o nome da imagem")
                    break

        except asyncio.TimeoutError:
            await ctx.send("Tempo limite excedido ao esperar a resposta do bot.")
        except requests.exceptions.RequestException as e:
            await ctx.send(f"Erro ao baixar a imagem: {e}")
        except Exception as e:
            await ctx.send(f"Ocorreu um erro: {e}")

    @commands.command(name="progresso")
    async def progresso_tema(self, ctx: commands.Context, tema: str = None):
        """Mostra o progresso de um tema ou o progresso geral dos temas."""

        if tema is None:
            # Mostrar progresso geral dos temas
            await self.mostrar_progresso_geral(ctx)
        else:
            # Mostrar progresso para um tema específico
            await self.mostrar_progresso_tema_especifico(ctx, tema)

    async def mostrar_progresso_geral(self, ctx: commands.Context):
        """Mostra o progresso geral dos temas."""

        try:
            temas = [d for d in os.listdir(self.temas_pasta) if os.path.isdir(os.path.join(self.temas_pasta, d))]
            total_temas = len(temas)

            # Get completed themes with correct capitalization
            temas_completos = []
            for tema_dir in self.completed_themes.keys():
                for tema in temas:
                    if tema.lower() == tema_dir.lower():  # Compare lowercase
                        temas_completos.append(tema)  # Append correctly capitalized name
                        break

            total_temas_completos = len(temas_completos)

            progresso_percentual = (total_temas_completos / total_temas) * 100 if total_temas > 0 else 0

            ultimo_tema_adicionado = temas_completos[-1] if temas_completos else "Nenhum tema completo"

            embed = discord.Embed(
                title="Progresso Geral dos Temas",
                color=discord.Color.green()
            )
            embed.add_field(name="Último Tema Completado:", value=ultimo_tema_adicionado, inline=False)
            embed.add_field(name="Progresso Atual:",
                            value=f"{progresso_percentual:.2f}% ({total_temas_completos}/{total_temas})",
                            inline=False)

            view = ProgressoGeralView(self, temas, temas_completos)
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            await ctx.send(f"Ocorreu um erro: {e}")

    async def mostrar_progresso_tema_especifico(self, ctx: commands.Context, tema: str):
        """Mostra o progresso para um tema específico."""
        try:
            caminho_tema = os.path.join(self.temas_pasta, tema)

            if not os.path.exists(caminho_tema):
                await ctx.send(f"Não encontrei a pasta do tema '{tema}'.")
                return

            # Encontra o nome correto da pasta
            tema_dir = os.path.basename(caminho_tema)

            nome_arquivo = f"lista_{tema_dir.lower().replace(' ', '_')}.txt"
            caminho_completo = os.path.join(caminho_tema, nome_arquivo)

            if not os.path.exists(caminho_completo):
                await ctx.send(f"Não encontrei a lista para o tema '{tema_dir}'.")
                return

            with open(caminho_completo, "r", encoding="utf-8") as f:
                lista_itens = [self.normalize_text(item.strip().lower()) for item in f.readlines()]

            imagens_pasta = os.path.join(self.temas_pasta, tema_dir)
            if not os.path.exists(imagens_pasta) or not os.listdir(imagens_pasta):
                await ctx.send(f"Não encontrei imagens para o tema '{tema_dir}'.")
                return
            nomes_imagens = [f for f in os.listdir(imagens_pasta) if f.lower().endswith(('.jpg', '.png'))]

            nomes_imagens_tratados = []
            for nome_imagem in nomes_imagens:
                nome_sem_extensao = os.path.splitext(nome_imagem)[0]
                nome_sem_mod = nome_sem_extensao.replace("mod ", "")

                if nome_sem_mod in self.modified_names:
                    nome_original = self.modified_names[nome_sem_mod]
                    nome_final = nome_original.replace(f"{tema_dir} ", "").lower()
                    nomes_imagens_tratados.append(self.normalize_text(nome_final))
                else:
                    nome_final = nome_sem_mod.replace(f"{tema_dir} ", "").lower()
                    nomes_imagens_tratados.append(self.normalize_text(nome_final))

            faltantes = [item for item in lista_itens if item not in nomes_imagens_tratados]

            adicionados = [item for item in lista_itens if item in nomes_imagens_tratados]

            total_itens = len(lista_itens)
            total_adicionados = len(adicionados)
            progresso_percentual = (total_adicionados / total_itens) * 100 if total_itens > 0 else 0

            ultimo_adicionado = adicionados[-1] if adicionados else "Nenhuma adicionada"
            proximo_item = faltantes[0] if faltantes else "Todas adicionadas"

            embed = discord.Embed(
                title=f"Progresso do tema: {tema_dir}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Última palavra adicionada:", value=ultimo_adicionado, inline=False)
            embed.add_field(name="Próxima palavra:", value=proximo_item, inline=False)
            embed.add_field(name="Progresso atual:",
                            value=f"{progresso_percentual:.2f}% ({total_adicionados}/{total_itens})",
                            inline=False)

            # Check if the theme is complete and update the completed themes list
            if not faltantes:
                if tema_dir not in self.completed_themes:
                    self.completed_themes[tema_dir] = True
                    self.save_completed_themes()
                    print(f"Tema '{tema_dir}' concluído e adicionado à lista de temas completos.")
                await ctx.send(embed=embed)  # Send only the embed when the theme is complete

            else:
                if tema_dir in self.completed_themes:
                    del self.completed_themes[tema_dir]
                    self.save_completed_themes()
                    print(f"Tema '{tema_dir}' não está completo e removido da lista de temas completos.")

                view = discord.ui.View()
                nao_adicionadas_button = discord.ui.Button(
                    style=discord.ButtonStyle.blurple,
                    label="Não Adicionadas"
                )
                nao_adicionadas_button.callback = lambda interaction: self.nao_adicionadas_callback(interaction, tema_dir, faltantes, ctx.author)
                view.add_item(nao_adicionadas_button)

                await ctx.send(embed=embed, view=view)

        except Exception as e:
           await ctx.send(f"Ocorreu um erro: {e}")
      
    @commands.command(name="temas")
    async def listar_temas(self, ctx: commands.Context):
        """Lista os temas, suas listas e o número de itens em cada lista."""
        await ctx.send("Verificando temas... Aguarde.")
        try:
            temas = sorted([d for d in os.listdir(self.temas_pasta) if os.path.isdir(os.path.join(self.temas_pasta, d))])
            relatorio = f"**Lista de temas: ({len(temas)} temas encontrados)**\n"
            for tema in temas:
                caminho_tema = os.path.join(self.temas_pasta, tema)
                nome_arquivo = f"lista_{tema.lower().replace(' ', '_')}.txt"
                caminho_completo = os.path.join(caminho_tema, nome_arquivo)
                
                if os.path.exists(caminho_completo):
                    with open(caminho_completo, "r", encoding="utf-8") as f:
                        lista_itens = f.readlines()
                    relatorio += f"\n- {tema}: {len(lista_itens)} itens."
                else:
                     relatorio += f"\n- {tema}: Não possui lista."

            if len(relatorio) > 2000:
                 parts = []
                 current_part = ""
                 lines = relatorio.splitlines(True)
                 for line in lines:
                      if len(current_part) + len(line) > 2000:
                            parts.append(current_part)
                            current_part = line
                      else:
                           current_part += line
                 parts.append(current_part)
                 for part in parts:
                      await ctx.send(part)
            else:
                await ctx.send(relatorio)
        except Exception as e:
           await ctx.send(f"Ocorreu um erro: {e}")

    async def nao_adicionadas_callback(self, interaction: discord.Interaction, tema: str, faltantes: list, author: discord.Member):
        """Callback para o botão 'Não Adicionadas'."""

        if interaction.user != author:
            await interaction.response.send_message("Você não pode usar este botão!", ephemeral=True)
            return

        # Cria a view de paginação
        view = PaginacaoTemasView(tema, faltantes, author, tipo="pendentes")
        await interaction.response.send_message(embed=view.gerar_embed(), view=view, ephemeral=True)

class PaginacaoTemasView(discord.ui.View):
    def __init__(self, tema: str, lista: list, author: discord.Member, tipo: str, per_page: int = 20):
        super().__init__(timeout=180)
        self.tema = tema
        self.lista = lista
        self.author = author
        self.tipo = tipo
        self.per_page = per_page
        self.current_page = 0
        self.total_pages = (len(self.lista) + self.per_page - 1) // self.per_page  # Cálculo correto do total de páginas

        self.update_buttons()

    def gerar_embed(self) -> discord.Embed:
        """Gera o embed com os itens da página atual."""

        start_index = self.current_page * self.per_page
        end_index = min(start_index + self.per_page, len(self.lista))  # Evita IndexError
        itens_pagina = self.lista[start_index:end_index]

        embed = discord.Embed(
            title=f"Temas {self.tipo.capitalize()} - Página {self.current_page + 1}/{self.total_pages}",
            color=discord.Color.orange()
        )

        # Divide os itens em duas colunas
        coluna1 = itens_pagina[:len(itens_pagina) // 2]
        coluna2 = itens_pagina[len(itens_pagina) // 2:]

        embed.add_field(name="Coluna 1", value="\n".join(coluna1) or "Vazio", inline=True)
        embed.add_field(name="Coluna 2", value="\n".join(coluna2) or "Vazio", inline=True)

        return embed

    def update_buttons(self):
        """Desabilita os botões de acordo com a página atual."""

        self.first_page_button.disabled = self.current_page == 0
        self.prev_page_button.disabled = self.current_page == 0
        self.next_page_button.disabled = self.current_page >= self.total_pages - 1
        self.last_page_button.disabled = self.current_page >= self.total_pages - 1

    @discord.ui.button(label="Primeira", style=discord.ButtonStyle.secondary, emoji="⏪")
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("Você não pode usar este botão!", ephemeral=True)
            return

        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.secondary, emoji="◀️")
    async def prev_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("Você não pode usar este botão!", ephemeral=True)
            return

        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

    @discord.ui.button(label="Próxima", style=discord.ButtonStyle.secondary, emoji="▶️")
    async def next_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("Você não pode usar este botão!", ephemeral=True)
            return

        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

    @discord.ui.button(label="Última", style=discord.ButtonStyle.secondary, emoji="⏩")
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("Você não pode usar este botão!", ephemeral=True)
            return

        self.current_page = self.total_pages - 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

class ProgressoGeralView(discord.ui.View):
    def __init__(self, cog, temas, temas_completos):
        super().__init__(timeout=180)
        self.cog = cog
        self.temas = temas
        self.temas_completos = temas_completos

    @discord.ui.button(label="Temas Pendentes", style=discord.ButtonStyle.blurple)
    async def temas_pendentes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get correctly capitalized pending themes
        temas_pendentes = [tema for tema in self.temas if tema not in self.temas_completos]
        view = PaginacaoTemasView("", temas_pendentes, interaction.user, "pendentes")
        await interaction.response.send_message(embed=view.gerar_embed(), view=view, ephemeral=True)

    @discord.ui.button(label="Temas Completos", style=discord.ButtonStyle.green)
    async def temas_completos_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get correctly capitalized complete themes
        view = PaginacaoTemasView("", self.temas_completos, interaction.user, "completos")
        await interaction.response.send_message(embed=view.gerar_embed(), view=view)
async def setup(bot):
    await bot.add_cog(TemasInteract(bot))