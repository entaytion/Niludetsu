import discord
from discord.ext import commands
import yaml
from typing import Optional, Dict, Any
from ..utils.embed import Embed

class SetupView(discord.ui.View):
    """View для меню настроек"""
    
    def __init__(self):
        super().__init__(timeout=None)
        
        # Добавляем кнопки
        self.add_item(RulesButton())
        self.add_item(CommandsButton())
        self.add_item(PartnershipButton())

class RulesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Правила сервера",
            emoji="📋",
            custom_id="rules"
        )
        
    async def callback(self, interaction: discord.Interaction):
        try:
            embed = Embed(
                title="📋 Правила сервера",
                description=(
                    "**[1]** Соблюдайте **конфиденциальность** личных данных других пользователей.\n"
                    "**[2]** Не размещайте **вредоносные ссылки, фишинговые попытки** или **вредоносные файлы**.\n"
                    "**[3]** Не допускайте **угроз, ненависти, дискриминации, расизма** или других форм оскорбительного поведения.\n"
                    "**[4]** Не размещайте **незаконный, оскорбительный, порнографический** или **неприемлемый контент** (исключая NSFW каналы).\n"
                    "**[5]** Не используйте **баги** или **недокументированные функции** Discord/ботов.\n"
                    "**[6]** Не выдавайте себя за **других людей** или **администраторов** и не вводите пользователей в **заблуждение**.\n"
                    "**[7]** Избегайте неконструктивного поведения, такого как **троллинг, флейм, провокация** и тому подобные.\n"
                    "**[8]** Не используйте сервер для **саморекламы** или **продвижения коммерческих услуг** без разрешения администрации.\n"
                    "**[9]** Не участвуйте в **спам-атаках**, **краш-атаках** или других попытках поставить под угрозу **стабильность** и/или **производительность** сервера.\n"
                    "**[10]** Не нарушайте **правила платформы Discord** и соблюдайте **условия** на сервере."
                ),
                color=0x2b2d31
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.errors.NotFound:
            # Игнорируем ошибку истекшего взаимодействия
            pass
        except Exception as e:
            print(f"Ошибка при обработке кнопки правил: {e}")

class CommandsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Команды ботов",
            emoji="⌨️",
            custom_id="commands"
        )
        
    async def callback(self, interaction: discord.Interaction):
        try:
            embed = Embed(
                title="⌨️ Команды ботов",
                description=(
                    "Для просмотра всех доступных команд используйте:\n"
                    "• `/help` - список всех команд и их описание"
                ),
                color=0x2b2d31
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.errors.NotFound:
            # Игнорируем ошибку истекшего взаимодействия
            pass
        except Exception as e:
            print(f"Ошибка при обработке кнопки команд: {e}")

class PartnershipButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Партнёрство с сервером",
            emoji="💼",
            custom_id="partnership"
        )
        
    async def callback(self, interaction: discord.Interaction):
        try:
            embed = Embed(
                title="💼 Партнёрство с сервером",
                description=(
                    "**Требования к серверам:**\n"
                    "• Отсутствие нарушений правил Discord\n\n"
                    "**Для заявки:**\n"
                    "Обратитесь к персоналу, который имеет роль \"Партнер-менеджер\" в сервере"
                ),
                color=0x2b2d31
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.errors.NotFound:
            # Игнорируем ошибку истекшего взаимодействия
            pass
        except Exception as e:
            print(f"Ошибка при обработке кнопки партнерства: {e}")

class SetupManager:
    """Менеджер интерактивного меню настроек"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Dict[str, Any] = {}
        self.load_config()
        
    def load_config(self) -> None:
        """Загружает конфигурацию из файла"""
        try:
            with open("data/config.yaml", "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.config = {}
            
    def save_config(self) -> None:
        """Сохраняет конфигурацию в файл"""
        try:
            with open("data/config.yaml", "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, indent=4, allow_unicode=True)
        except Exception as e:
            print(f"Ошибка при сохранении конфига: {e}")
            
    async def get_setup_message(self) -> Optional[discord.Message]:
        """Получает сообщение с меню настроек"""
        channel_id = self.config.get("setup", {}).get("channel")
        message_id = self.config.get("setup", {}).get("message")
                
        if not channel_id:
            return None
            
        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return None
                
            if not message_id:
                return None
                
            message = await channel.fetch_message(int(message_id))
            return message
        except Exception as e:
            return None
            
    async def create_setup_message(self) -> Optional[discord.Message]:
        """Создает новое сообщение с меню настроек"""
        channel_id = self.config.get("setup", {}).get("channel")

        if not channel_id:
            return None
            
        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return None
                
            # Создаем базовый эмбед
            embed = Embed(
                title="Информация", 
                description="Нажмите на кнопку, для того чтобы ознакомиться с правилами,\nкомандами и возможностями нашего сервера!",
                color=0x2b2d31
            )
            embed.set_image(url="https://cdn.discordapp.com/attachments/1332296613988794450/1335578470692163715/bgggg.png")
            
            # Создаем и отправляем сообщение с меню
            message = await channel.send(embed=embed, view=SetupView())
            
            # Сохраняем ID сообщения в конфиг
            if "setup" not in self.config:
                self.config["setup"] = {}
            self.config["setup"]["message"] = str(message.id)
            self.save_config()
            
            return message
        except Exception as e:
            return None
            
    async def initialize(self) -> None:
        """Инициализирует меню настроек"""
        
        # Пытаемся получить существующее сообщение
        message = await self.get_setup_message()
        
        # Если сообщение не найдено, создаем новое
        if not message:
            await self.create_setup_message()
        else:
            # Если сообщение существует, обновляем его
            try:
                embed = Embed(
                    title="Информация",
                    description="Нажмите на кнопку, для того чтобы ознакомиться с правилами,\nкомандами и возможностями нашего сервера!",
                    color=0x2b2d31
                )
                embed.set_image(url="https://cdn.discordapp.com/attachments/1332296613988794450/1335578470692163715/bgggg.png?ex=67a0ade1&is=679f5c61&hm=dde65f9dd32b461c60df190987f3cecf7813bc0266e6bd821d09a1ee5bfd35b5&")
                await message.edit(embed=embed, view=SetupView())
            except Exception as e:
                await self.create_setup_message() 