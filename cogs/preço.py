import discord
from discord import app_commands
from discord.ext import commands

class Preço(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

        self.precos = {
            1: 10, 2: 20, 3: 50, 4: 80, 5: 130, 6: 180, 7: 250, 8: 320, 9: 410, 10: 500,
            11: 610, 12: 720, 13: 850, 14: 980, 15: 1130, 16: 1280, 17: 1450, 18: 1620, 19: 1810, 20: 2000,
            21: 2210, 22: 2420, 23: 2650, 24: 2880, 25: 3130, 26: 3380, 27: 3650, 28: 3920, 29: 4210, 30: 4500,
            31: 4810, 32: 5120, 33: 5450, 34: 5780, 35: 6130, 36: 6480, 37: 6850, 38: 7220, 39: 7610, 40: 8000,
            41: 8410, 42: 8820, 43: 9250, 44: 9680, 45: 10130, 46: 10580, 47: 11050, 48: 11520, 49: 12010, 50: 12500,
            51: 13010, 52: 13520, 53: 14050, 54: 14580, 55: 15130, 56: 15680, 57: 16250, 58: 16820, 59: 17410, 60: 18000,
            61: 18610, 62: 19220, 63: 19850, 64: 20480, 65: 21130, 66: 21780, 67: 22450, 68: 23120, 69: 23810, 70: 24500,
            71: 25210, 72: 25920, 73: 26650, 74: 27380, 75: 28130, 76: 28880, 77: 29650, 78: 30420, 79: 31210, 80: 32000,
            81: 32810, 82: 33620, 83: 34450, 84: 35280, 85: 36130, 86: 36980, 87: 37850, 88: 38720, 89: 39610, 90: 40500,
            91: 41410, 92: 42320, 93: 43250, 94: 44180, 95: 45130, 96: 46080, 97: 47050, 98: 48020, 99: 49010, 100: 50000,
            101: 51010, 102: 52020, 103: 53050, 104: 54080, 105: 55130, 106: 56180, 107: 57250, 108: 58320, 109: 59410, 110: 60500,
            111: 61610, 112: 62720, 113: 63850, 114: 64980, 115: 66130, 116: 67280, 117: 68450, 118: 69620, 119: 70810, 120: 72000,
            121: 73210, 122: 74420, 123: 75650, 124: 76880, 125: 78130, 126: 79380, 127: 80650, 128: 81920, 129: 83210, 130: 84500,
            131: 85810, 132: 87120, 133: 88450, 134: 89780, 135: 91130, 136: 92480, 137: 93850, 138: 95220, 139: 96610, 140: 98000,
            141: 99410, 142: 100820, 143: 102250, 144: 103680, 145: 105130, 146: 106580, 147: 108050, 148: 109520, 149: 111010, 150: 112500,
            151: 114010, 152: 115520, 153: 117050, 154: 118580, 155: 120130, 156: 121680, 157: 123250, 158: 124820, 159: 126410, 160: 128000,
            161: 129610, 162: 131220, 163: 132850, 164: 134480, 165: 136130, 166: 137780, 167: 139450, 168: 141120, 169: 142810, 170: 144500,
            171: 146210, 172: 147920, 173: 149650, 174: 151380, 175: 153130, 176: 154880, 177: 156650, 178: 158420, 179: 160210, 180: 162000,
            181: 163810, 182: 165620, 183: 167450, 184: 169280, 185: 171130, 186: 172980, 187: 174850, 188: 176720, 189: 178610, 190: 180500,
            191: 182410, 192: 184320, 193: 186250, 194: 188180, 195: 190130, 196: 192080, 197: 194050, 198: 196020, 199: 198010, 200: 200000,
            201: 202010, 202: 204020, 203: 206050, 204: 208080, 205: 210130, 206: 212180, 207: 214250, 208: 216320, 209: 218410, 210: 220500,
            211: 222610, 212: 224720, 213: 226850, 214: 228980, 215: 231130, 216: 233280, 217: 235450, 218: 237620, 219: 239810, 220: 242000,
            221: 244210, 222: 246420, 223: 248650, 224: 250880, 225: 253130, 226: 255380, 227: 257650, 228: 259920, 229: 262210, 230: 264500,
            231: 266810, 232: 269120, 233: 271450, 234: 273780, 235: 276130, 236: 278480, 237: 280850, 238: 283220, 239: 285610, 240: 288000,
            241: 290410, 242: 292820, 243: 295250, 244: 297680, 245: 300130, 246: 302580, 247: 305050, 248: 307520, 249: 310010, 250: 312500,
            251: 315010, 252: 317520, 253: 320050, 254: 322580, 255: 325130, 256: 327680, 257: 330250, 258: 332820, 259: 335410, 260: 338000,
            261: 340610, 262: 343220, 263: 345850, 264: 348480, 265: 351130, 266: 353780, 267: 356450, 268: 359120, 269: 361810, 270: 364500,
            271: 367210, 272: 369920, 273: 372650, 274: 375380, 275: 378130, 276: 380880, 277: 383650, 278: 386420, 279: 389210, 280: 392000,
            281: 394810, 282: 397620, 283: 400450, 284: 403280, 285: 406130, 286: 408980, 287: 411850, 288: 414720, 289: 417610, 290: 420500,
            291: 423410, 292: 426320, 293: 429250, 294: 432180, 295: 435130, 296: 438080, 297: 441050, 298: 444020, 299: 447010, 300: 450000,
            301: 453010, 302: 456020, 303: 459050, 304: 462080, 305: 465130, 306: 468180, 307: 471250, 308: 474320, 309: 477410, 310: 480500,
            311: 483610, 312: 486720, 313: 489850, 314: 492980, 315: 496130, 316: 499280, 317: 502450, 318: 505620, 319: 508810, 320: 512000,
            321: 515210, 322: 518420, 323: 521650, 324: 524880, 325: 528130, 326: 531380, 327: 534650, 328: 537920, 329: 541210, 330: 544500,
            331: 547810, 332: 551120, 333: 554450, 334: 557780, 335: 561130, 336: 564480, 337: 567850, 338: 571220, 339: 574610, 340: 578000,
            341: 581410, 342: 584820, 343: 588250, 344: 591680, 345: 595130, 346: 598580, 347: 602050, 348: 605520, 349: 609010, 350: 612500,
            351: 616010, 352: 619520, 353: 623050, 354: 626580, 355: 630130, 356: 633680, 357: 637250, 358: 640820, 359: 644410, 360: 648000,
            361: 651610, 362: 655220, 363: 658850, 364: 662480, 365: 666130, 366: 669780, 367: 673450, 368: 677120, 369: 680810, 370: 684500,
            371: 688210, 372: 691920, 373: 695650, 374: 699380, 375: 703130, 376: 706880, 377: 710650, 378: 714420, 379: 718210, 380: 722000,
            381: 725810, 382: 729620, 383: 733450, 384: 737280, 385: 741130, 386: 744980, 387: 748850, 388: 752720, 389: 756610, 390: 760500,
            391: 764410, 392: 768320, 393: 772250, 394: 776180, 395: 780130, 396: 784080, 397: 788050, 398: 792020, 399: 796010, 400: 800000
        }
        self.items_per_page = 10

    def _get_closest_level(self, price):
        """Retorna o nível mais próximo do preço fornecido."""
        closest_level = None
        min_diff = float('inf')
        for level, preco in self.precos.items():
            diff = abs(preco - price)
            if diff < min_diff:
                min_diff = diff
                closest_level = level
        return closest_level

    def _get_page_content(self, page_num):
        """Retorna o conteúdo para uma página específica."""
        start_index = (page_num - 1) * self.items_per_page + 1
        end_index = min(start_index + self.items_per_page, len(self.precos) + 1)

        content = {}
        for i in range(start_index, end_index):
            if i in self.precos:
                content[i] = self.precos[i]
        return content

    async def _create_embed(self, page_content, current_page, total_pages, searched_price=None, closest_level=None):
        """Cria o embed."""
        embed = discord.Embed(title="Tabela de Preços", color=discord.Color.blue())
        embed.set_footer(text=f"Página {current_page}/{total_pages}")

        level_field = ""
        price_field = ""

        for level, price in page_content.items():
            level_field += f"{level}\n"
            price_field += f"{price:,.0f}\n".replace(",", ".")

        if searched_price and closest_level in page_content:
            level_field = level_field.replace(str(closest_level), f"**{closest_level}**")
            price_field = price_field.replace(f"{page_content[closest_level]:,.0f}".replace(",", "."), f"**{page_content[closest_level]:,.0f}**".replace(",", "."))

        embed.add_field(name="Nível", value=level_field or "Vazio", inline=True)
        embed.add_field(name="Preço", value=price_field or "Vazio", inline=True)
        return embed

    class Paginator(discord.ui.View):
        def __init__(self, cog, interaction, price, closest_level, total_pages, initial_content):
            super().__init__()
            self.cog = cog
            self.interaction = interaction
            self.price = price
            self.closest_level = closest_level
            self.total_pages = total_pages
            self.current_page = (closest_level - 1) // cog.items_per_page + 1 if closest_level else 1  # Calcula a página inicial
            self.initial_content = initial_content

            # Desabilita os botões se estiver na primeira ou última página
            self.update_buttons()

        async def update_message(self):
            if self.current_page == ((self.closest_level - 1) // self.cog.items_per_page + 1 if self.closest_level else 1) and self.initial_content:
                content = self.initial_content
                searched_price = self.price
                closest_level = self.closest_level
                self.initial_content = None  # Limpa para não usar novamente
            else:
                content = self.cog._get_page_content(self.current_page)
                searched_price = None
                closest_level = None
            
            embed = await self.cog._create_embed(
                content, self.current_page, self.total_pages, searched_price, closest_level
            )
            await self.interaction.edit_original_response(embed=embed, view=self)
            self.update_buttons()  # Atualiza o estado dos botões após a edição

        def update_buttons(self):
            self.previous_button.disabled = self.current_page == 1
            self.next_button.disabled = self.current_page == self.total_pages

        @discord.ui.button(label="Anterior", style=discord.ButtonStyle.primary)
        async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()  # Acknowledge the interaction
            self.current_page -= 1
            await self.update_message()

        @discord.ui.button(label="Próxima", style=discord.ButtonStyle.primary)
        async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()  # Acknowledge the interaction
            self.current_page += 1
            await self.update_message()


    @app_commands.command(name="precos", description="Mostra os preços próximos ao valor especificado.")
    @app_commands.describe(valor="O valor para pesquisar (ex: 200 ou 35k).")
    async def precos(self, interaction: discord.Interaction, valor: str):
        try:
            valor = valor.lower().replace("k", "000")
            price = int(valor)
        except ValueError:
            await interaction.response.send_message("Valor inválido. Use um número inteiro ou um número seguido de 'k' (ex: 35k).", ephemeral=True)
            return

        closest_level = self._get_closest_level(price)

        # Calcula a página onde o nível mais próximo está
        page_num = (closest_level - 1) // self.items_per_page + 1 if closest_level else 1
        total_pages = (len(self.precos) + self.items_per_page - 1) // self.items_per_page

        # Cria o conteúdo inicial com 5 itens antes e depois do nível mais próximo
        start_level = max(1, closest_level - 5)
        end_level = min(len(self.precos), closest_level + 5)
        initial_content = {level: self.precos[level] for level in range(start_level, end_level + 1) if level in self.precos}

        # Cria o embed inicial
        embed = await self._create_embed(initial_content, page_num, total_pages, price, closest_level)

        # Inicializa a paginação com o Paginator
        paginator = self.Paginator(self, interaction, price, closest_level, total_pages, initial_content)
        await interaction.response.send_message(embed=embed, view=paginator)

async def setup(bot):
    await bot.add_cog(Preço(bot))