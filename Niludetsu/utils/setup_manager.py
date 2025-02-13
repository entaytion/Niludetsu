import discord
from discord.ext import commands
import yaml
from typing import Optional, Dict, Any, List
from .embed import Embed

class SetupView(discord.ui.View):
    """View для меню настроек"""
    
    def __init__(self):
        super().__init__(timeout=None)
        
        # Добавляем кнопки в первый ряд
        rules_btn = RulesButton()
        rules_btn.row = 0
        self.add_item(rules_btn)
        
        commands_btn = CommandsButton()
        commands_btn.row = 0
        self.add_item(commands_btn)
        
        partnership_btn = PartnershipButton()
        partnership_btn.row = 0
        self.add_item(partnership_btn)
        
        # Добавляем кнопки во второй ряд
        color_btn = ColorRoleButton()
        color_btn.row = 1
        self.add_item(color_btn)
        
        gender_btn = GenderRoleButton()
        gender_btn.row = 1
        self.add_item(gender_btn)

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

class ColorRoleButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Выбрать цвет роли",
            emoji="🎨",
            custom_id="color_role"
        )
        
    async def callback(self, interaction: discord.Interaction):
        try:
            # Создаем эмбед с превью цветов
            embed = Embed(
                title="🎨 Выбор цвета роли",
                description="Нажмите на кнопку, чтобы выбрать цвет вашей роли:",
                color=0x2b2d31
            )
            
            # Загружаем цвета для отображения в эмбеде
            with open("data/config.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                colors = config.get("color_roles", {}).get("roles", [])
            
            # Создаем превью цветов с пингами ролей
            preview = ""
            for color in colors:
                role_id = color.get("id")
                if role_id:
                    preview += f"{color['emoji']} <@&{role_id}>\n"
                else:
                    # Создаем роль если её нет
                    role = await interaction.guild.create_role(
                        name=color["name"],
                        color=discord.Color(color["color"]),
                        reason="Создание цветной роли"
                    )
                    color["id"] = str(role.id)
                    preview += f"{color['emoji']} <@&{role.id}>\n"
                    # Сохраняем ID роли в конфиг
                    with open("data/config.yaml", "w", encoding="utf-8") as f:
                        yaml.dump(config, f, indent=4, allow_unicode=True)
            
            embed.description = f"Нажмите на кнопку, чтобы выбрать цвет вашей роли:\n\n{preview}"
            
            await interaction.response.send_message(
                embed=embed,
                view=ColorRoleSelectView(),
                ephemeral=True
            )
        except Exception as e:
            print(f"Ошибка при обработке кнопки выбора цвета: {e}")
            await interaction.response.send_message(
                "Произошла ошибка при отображении цветов. Пожалуйста, обратитесь к администрации.",
                ephemeral=True
            )

class ColorRoleSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        
        # Загружаем цвета из конфига
        with open("data/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            colors = config.get("color_roles", {}).get("roles", [])
        
        # Добавляем кнопки цветов в три ряда по 5 кнопок
        for i, color_data in enumerate(colors):
            button = ColorButton(
                name=color_data["name"],
                emoji=color_data["emoji"],
                color_hex=color_data["color"]
            )
            # Распределяем по рядам: первые 5 в первый ряд, следующие 5 во второй и т.д.
            row = i // 5
            button.row = row
            self.add_item(button)

class ColorButton(discord.ui.Button):
    def __init__(self, name: str, emoji: str, color_hex: int):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="",  # Пустой label для эстетики
            emoji=emoji,
            custom_id=f"color_{name}"
        )
        self.role_name = name
        self.color_hex = color_hex
    
    def set_row(self, row: int) -> 'ColorButton':
        """Устанавливает ряд для кнопки и возвращает её"""
        self.row = row
        return self
        
    async def callback(self, interaction: discord.Interaction):
        try:
            # Загружаем конфиг для получения ID ролей
            with open("data/config.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                color_roles = config.get("color_roles", {}).get("roles", [])
                
            # Находим данные нашей роли в конфиге
            role_data = next((role for role in color_roles if role["name"] == self.role_name), None)
            if not role_data:
                await interaction.response.send_message(
                    "Ошибка: роль не найдена в конфигурации.",
                    ephemeral=True
                )
                return
                
            # Получаем роль по ID или создаем новую
            role = None
            if role_data["id"]:
                role = interaction.guild.get_role(int(role_data["id"]))
                
            if not role:
                # Создаем новую роль
                role = await interaction.guild.create_role(
                    name=self.role_name,
                    color=discord.Color(self.color_hex),
                    reason="Создание цветной роли"
                )
                
                # Сохраняем ID роли в конфиг
                role_data["id"] = str(role.id)
                with open("data/config.yaml", "w", encoding="utf-8") as f:
                    yaml.dump(config, f, indent=4, allow_unicode=True)
            
            # Удаляем все другие цветные роли у пользователя
            user_roles_to_remove = []
            for member_role in interaction.user.roles:
                for color_role in color_roles:
                    if color_role["id"] and str(member_role.id) == str(color_role["id"]):
                        user_roles_to_remove.append(member_role)
                        break
            
            if user_roles_to_remove:
                await interaction.user.remove_roles(*user_roles_to_remove)
            
            # Выдаем новую роль
            await interaction.user.add_roles(role)
            
            embed = Embed(
                title="🎨 Смена цвета",
                description=f"Вы успешно выбрали цвет {self.role_name}",
                color=self.color_hex
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            print(f"Ошибка при выдаче цветной роли: {e}")
            await interaction.response.send_message(
                "Произошла ошибка при выдаче роли. Пожалуйста, обратитесь к администрации.",
                ephemeral=True
            )

class GenderRoleButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Выбрать пол",
            emoji="👥",
            custom_id="gender_role"
        )
        
    async def callback(self, interaction: discord.Interaction):
        try:
            # Создаем эмбед с превью гендерных ролей
            embed = Embed(
                title="👥 Выбор пола",
                description="Нажмите на кнопку, чтобы выбрать свой пол:",
                color=0x2b2d31
            )
            
            # Загружаем роли для отображения в эмбеде
            with open("data/config.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                genders = config.get("gender_roles", {}).get("roles", [])
            
            # Создаем превью ролей с пингами
            preview = ""
            for gender in genders:
                role_id = gender.get("id")
                if role_id:
                    preview += f"{gender['emoji']} <@&{role_id}>\n"
            
            embed.description = f"Нажмите на кнопку, чтобы выбрать свой пол:\n\n{preview}"
            
            # Используем отдельное меню для гендеров
            await interaction.response.send_message(
                embed=embed,
                view=GenderRoleSelectView(),
                ephemeral=True
            )
        except Exception as e:
            print(f"Ошибка при отображении выбора пола: {e}")
            await interaction.response.send_message(
                "Произошла ошибка при отображении ролей. Пожалуйста, обратитесь к администрации.",
                ephemeral=True
            )

class GenderRoleSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        
        # Загружаем гендеры из конфига
        with open("data/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            genders = config.get("gender_roles", {}).get("roles", [])
        
        # Добавляем кнопки гендера в один ряд
        for i, gender_data in enumerate(genders):
            button = GenderButton(
                name=gender_data["name"],
                emoji=gender_data["emoji"],
                role_id=gender_data["id"]
            )
            self.add_item(button.set_row(0))  # Один ряд

class GenderButton(discord.ui.Button):
    def __init__(self, name: str, emoji: str, role_id: str):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="",  # Пустой label для эстетики
            emoji=emoji,
            custom_id=f"gender_{name}"
        )
        self.role_name = name
        self.role_id = role_id
    
    def set_row(self, row: int) -> 'GenderButton':
        """Устанавливает ряд для кнопки и возвращает её"""
        self.row = row
        return self
        
    async def callback(self, interaction: discord.Interaction):
        try:
            # Получаем роль по ID
            role = interaction.guild.get_role(int(self.role_id))
            if not role:
                await interaction.response.send_message(
                    "Ошибка: роль не найдена. Пожалуйста, обратитесь к администрации.",
                    ephemeral=True
                )
                return
                
            # Загружаем конфиг для получения всех гендерных ролей
            with open("data/config.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                gender_roles = config.get("gender_roles", {}).get("roles", [])
            
            # Удаляем все другие гендерные роли у пользователя
            user_roles_to_remove = []
            for member_role in interaction.user.roles:
                for gender_role in gender_roles:
                    if gender_role["id"] and str(member_role.id) == str(gender_role["id"]):
                        user_roles_to_remove.append(member_role)
                        break
            
            if user_roles_to_remove:
                await interaction.user.remove_roles(*user_roles_to_remove)
            
            # Выдаем новую роль
            await interaction.user.add_roles(role)
            
            embed = Embed(
                title="👥 Выбор пола",
                description=f"Вы успешно выбрали пол {self.role_name}",
                color=0x2b2d31
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            print(f"Ошибка при выдаче гендерной роли: {e}")
            await interaction.response.send_message(
                "Произошла ошибка при выдаче роли. Пожалуйста, обратитесь к администрации.",
                ephemeral=True
            )

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
            
    async def initialize_color_roles(self, guild: discord.Guild) -> None:
        """Инициализирует цветные роли на сервере"""
        try:
            color_roles = self.config.get("color_roles", {}).get("roles", [])
            
            for role_data in color_roles:
                role_name = role_data["name"]
                role_color = role_data["color"]
                role_id = role_data.get("id")
                
                role = None
                if role_id:
                    role = guild.get_role(int(role_id))
                
                if not role:
                    # Создаем роль если она не существует
                    role = await guild.create_role(
                        name=role_name,
                        color=discord.Color(role_color),
                        reason="Инициализация цветной роли"
                    )
                    # Сохраняем ID роли в конфиг
                    role_data["id"] = str(role.id)
                    self.save_config()
                    print(f"Создана цветная роль: {role_name} (ID: {role.id})")
                else:
                    # Обновляем название и цвет существующей роли если они отличаются
                    if role.name != role_name or role.color.value != role_color:
                        await role.edit(
                            name=role_name,
                            color=discord.Color(role_color),
                            reason="Обновление цветной роли"
                        )
                        print(f"Обновлена роль {role_name} (ID: {role.id})")
                        
        except Exception as e:
            print(f"Ошибка при инициализации цветных ролей: {e}")
    
    async def initialize(self) -> None:
        """Инициализирует меню настроек"""
        
        # Инициализируем цветные роли для каждого сервера
        for guild in self.bot.guilds:
            await self.initialize_color_roles(guild)
        
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
                embed.set_image(url="https://cdn.discordapp.com/attachments/1332296613988794450/1335578470692163715/bgggg.png")
                await message.edit(embed=embed, view=SetupView())
            except Exception as e:
                await self.create_setup_message() 