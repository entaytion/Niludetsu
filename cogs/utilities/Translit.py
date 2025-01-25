import discord
from discord import app_commands
from discord.ext import commands

class Translit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translit_dict = {
            'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е',
            'yo': 'ё', 'zh': 'ж', 'z': 'з', 'i': 'и', 'j': 'й', 'k': 'к',
            'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р',
            's': 'с', 't': 'т', 'u': 'у', 'f': 'ф', 'h': 'х', 'ts': 'ц',
            'ch': 'ч', 'sh': 'ш', 'sch': 'щ', 'y': 'ы', 'e': 'е', 'yu': 'ю',
            'ya': 'я', "'": 'ь', '#': 'ъ',
            # Украинские буквы (используем уникальные комбинации)
            'yi': 'ї', 'ye': 'є', 'ih': 'і', 'g\'': 'ґ',
            # Добавляем заглавные буквы
            'A': 'А', 'B': 'Б', 'V': 'В', 'G': 'Г', 'D': 'Д', 'E': 'Е',
            'Yo': 'Ё', 'Zh': 'Ж', 'Z': 'З', 'I': 'И', 'J': 'Й', 'K': 'К',
            'L': 'Л', 'M': 'М', 'N': 'Н', 'O': 'О', 'P': 'П', 'R': 'Р',
            'S': 'С', 'T': 'Т', 'U': 'У', 'F': 'Ф', 'H': 'Х', 'Ts': 'Ц',
            'Ch': 'Ч', 'Sh': 'Ш', 'Sch': 'Щ', 'Y': 'Ы', 'E': 'Е', 'Yu': 'Ю',
            'Ya': 'Я',
            # Украинские заглавные буквы
            'Yi': 'Ї', 'Ye': 'Є', 'Ih': 'І', 'G\'': 'Ґ'
        }
        
        self.layout_dict = {
            'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н',
            'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ',
            'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р',
            'j': 'о', 'k': 'л', 'l': 'д', ';': 'ж', "'": 'э', '\\': 'ё',
            'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т',
            'm': 'ь', ',': 'б', '.': 'ю', '/': '.',
            # Заглавные буквы
            'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н',
            'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З', '{': 'Х', '}': 'Ъ',
            'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р',
            'J': 'О', 'K': 'Л', 'L': 'Д', ':': 'Ж', '"': 'Э', '|': 'Ё',
            'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М', 'B': 'И', 'N': 'Т',
            'M': 'Ь', '<': 'Б', '>': 'Ю', '?': ',',
            # Украинские буквы
            ']': 'ї', # ї
            '}': 'Ї', # Ї
            "'": 'є', # є
            '"': 'Є', # Є
            '@': 'і', # і
            '#': 'І', # І
            '&': 'ґ', # ґ
            '^': 'Ґ'  # Ґ
        }

    def transliterate(self, text: str) -> str:
        result = ''
        i = 0
        while i < len(text):
            # Проверяем комбинации из трех символов
            if i + 2 < len(text) and text[i:i+3].lower() == 'sch':
                result += 'Щ' if text[i].isupper() else 'щ'
                i += 3
                continue
            
            # Проверяем комбинации из двух символов
            if i + 1 < len(text):
                combo = text[i:i+2]
                combo_lower = combo.lower()
                if combo_lower in ['yo', 'zh', 'ts', 'ch', 'sh', 'yu', 'ya']:
                    if combo[0].isupper():
                        result += self.translit_dict[combo_lower].upper()
                    else:
                        result += self.translit_dict[combo_lower]
                    i += 2
                    continue

            # Проверяем одиночные символы
            char = text[i]
            char_lower = char.lower()
            if char_lower in self.translit_dict:
                if char.isupper():
                    result += self.translit_dict[char_lower].upper()
                else:
                    result += self.translit_dict[char_lower]
            else:
                result += char
            i += 1

        return result

    def fix_layout(self, text: str) -> str:
        result = ''
        for char in text:
            if char in self.layout_dict:
                result += self.layout_dict[char]
            else:
                result += char
        return result

    @app_commands.command(name="t", description="Транслитерация текста с латиницы на кириллицу")
    @app_commands.describe(text="Текст для транслитерации")
    async def translit(self, interaction: discord.Interaction, text: str):
        try:
            translated = self.transliterate(text)
            embed = discord.Embed(
                title="🔄 Транслитерация",
                color=0x2F3136
            )
            embed.add_field(
                name="Исходный текст:",
                value=f"```{text}```",
                inline=False
            )
            embed.add_field(
                name="Результат:",
                value=f"```{translated}```",
                inline=False
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"❌ Произошла ошибка при транслитерации: {str(e)}",
                    color=0xFF0000
                ),
                ephemeral=True
            )

    @app_commands.command(name="k", description="Исправление текста, набранного в неправильной раскладке")
    @app_commands.describe(text="Текст для исправления")
    async def keyboard(self, interaction: discord.Interaction, text: str):
        try:
            fixed = self.fix_layout(text)
            embed = discord.Embed(
                title="⌨️ Исправление раскладки",
                color=0x2F3136
            )
            embed.add_field(
                name="Исходный текст:",
                value=f"```{text}```",
                inline=False
            )
            embed.add_field(
                name="Результат:",
                value=f"```{fixed}```",
                inline=False
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"❌ Произошла ошибка при исправлении раскладки: {str(e)}",
                    color=0xFF0000
                ),
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Translit(bot)) 