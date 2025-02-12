import discord
from discord.ext import commands
import yaml
from typing import Optional, Dict, Any, List
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis

class ColorRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        
        with open("data/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            colors = config.get("color_roles", {}).get("roles", [])
        
        for i, color_data in enumerate(colors):
            button = ColorButton(
                name=color_data["name"],
                emoji=color_data["emoji"],
                color_hex=color_data["color"]
            )
            row = i // 5
            button.row = row
            self.add_item(button)

class ColorButton(discord.ui.Button):
    def __init__(self, name: str, emoji: str, color_hex: int):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="",
            emoji=emoji,
            custom_id=f"color_{name}"
        )
        self.role_name = name
        self.color_hex = color_hex
    
    def set_row(self, row: int) -> 'ColorButton':
        self.row = row
        return self
        
    async def callback(self, interaction: discord.Interaction):
        try:
            with open("data/config.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                color_roles = config.get("color_roles", {}).get("roles", [])
                
            role_data = next((role for role in color_roles if role["name"] == self.role_name), None)
            if not role_data:
                await interaction.response.send_message(
                    "Ошибка: роль не найдена в конфигурации.",
                    ephemeral=True
                )
                return
                
            role = None
            if role_data.get("id"):
                role = interaction.guild.get_role(int(role_data["id"]))
                
            if not role:
                role = await interaction.guild.create_role(
                    name=self.role_name,
                    color=discord.Color(self.color_hex),
                    reason="Создание цветной роли"
                )
                role_data["id"] = str(role.id)
                with open("data/config.yaml", "w", encoding="utf-8") as f:
                    yaml.dump(config, f, indent=4, allow_unicode=True)
            
            member = interaction.user
            
            # Удаляем все цветные роли
            for color_role in color_roles:
                if color_role.get("id"):
                    role_to_remove = interaction.guild.get_role(int(color_role["id"]))
                    if role_to_remove and role_to_remove in member.roles:
                        await member.remove_roles(role_to_remove)
            
            # Добавляем выбранную роль
            await member.add_roles(role)
            await interaction.response.send_message(
                f"Вы выбрали цвет {role.mention}!",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"Ошибка при выборе цвета: {e}")
            await interaction.response.send_message(
                "Произошла ошибка при выборе цвета. Пожалуйста, обратитесь к администрации.",
                ephemeral=True
            )

class GenderRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        
        with open("data/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            genders = config.get("gender_roles", {}).get("roles", [])
        
        for i, gender_data in enumerate(genders):
            button = GenderButton(
                name=gender_data["name"],
                emoji=gender_data["emoji"],
                role_id=gender_data.get("id", "")
            )
            button.row = i // 2
            self.add_item(button)

class GenderButton(discord.ui.Button):
    def __init__(self, name: str, emoji: str, role_id: str):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=name,
            emoji=emoji,
            custom_id=f"gender_{name}"
        )
        self.role_name = name
        self.role_id = role_id
    
    def set_row(self, row: int) -> 'GenderButton':
        self.row = row
        return self
        
    async def callback(self, interaction: discord.Interaction):
        try:
            with open("data/config.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                gender_roles = config.get("gender_roles", {}).get("roles", [])
            
            role_data = next((role for role in gender_roles if role["name"] == self.role_name), None)
            if not role_data:
                await interaction.response.send_message(
                    "Ошибка: роль не найдена в конфигурации.",
                    ephemeral=True
                )
                return
            
            role = None
            if role_data.get("id"):
                role = interaction.guild.get_role(int(role_data["id"]))
            
            if not role:
                role = await interaction.guild.create_role(
                    name=self.role_name,
                    reason="Создание гендерной роли"
                )
                role_data["id"] = str(role.id)
                with open("data/config.yaml", "w", encoding="utf-8") as f:
                    yaml.dump(config, f, indent=4, allow_unicode=True)
            
            member = interaction.user
            
            # Удаляем все гендерные роли
            for gender_role in gender_roles:
                if gender_role.get("id"):
                    role_to_remove = interaction.guild.get_role(int(gender_role["id"]))
                    if role_to_remove and role_to_remove in member.roles:
                        await member.remove_roles(role_to_remove)
            
            # Добавляем выбранную роль
            await member.add_roles(role)
            await interaction.response.send_message(
                f"Вы выбрали пол {role.mention}!",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"Ошибка при выборе пола: {e}")
            await interaction.response.send_message(
                "Произошла ошибка при выборе пола. Пожалуйста, обратитесь к администрации.",
                ephemeral=True
            )

class RoleSelectView(discord.ui.View):
    """View для меню выбора ролей"""
    def __init__(self):
        super().__init__(timeout=None)
        
        # Добавляем кнопки в первый ряд
        color_btn = RoleButton(
            style=discord.ButtonStyle.secondary,
            label="Цветные роли",
            emoji="🎨",
            custom_id="color_role"
        )
        color_btn.row = 0
        self.add_item(color_btn)
        
        gender_btn = RoleButton(
            style=discord.ButtonStyle.secondary,
            label="Гендерные роли",
            emoji="👤",
            custom_id="gender_role"
        )
        gender_btn.row = 0
        self.add_item(gender_btn)

class RoleButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        try:
            if self.custom_id == "color_role":
                # Показываем меню выбора цвета
                embed = Embed(
                    title="🎨 Выбор цвета роли",
                    description="Нажмите на кнопку, чтобы выбрать цвет вашей роли:",
                    color=0x2b2d31
                )
                
                with open("data/config.yaml", "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    colors = config.get("color_roles", {}).get("roles", [])
                
                preview = ""
                for color in colors:
                    role_id = color.get("id")
                    if role_id:
                        preview += f"{color['emoji']} <@&{role_id}>\n"
                
                embed.description = f"Нажмите на кнопку, чтобы выбрать цвет вашей роли:\n\n{preview}"
                
                await interaction.response.send_message(
                    embed=embed,
                    view=ColorRoleView(),
                    ephemeral=True
                )
                
            elif self.custom_id == "gender_role":
                # Показываем меню выбора пола
                embed = Embed(
                    title="👤 Выбор пола",
                    description="Нажмите на кнопку, чтобы выбрать ваш пол:",
                    color=0x2b2d31
                )
                
                with open("data/config.yaml", "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    genders = config.get("gender_roles", {}).get("roles", [])
                
                preview = ""
                for gender in genders:
                    role_id = gender.get("id")
                    if role_id:
                        preview += f"{gender['emoji']} <@&{role_id}>\n"
                
                embed.description = f"Нажмите на кнопку, чтобы выбрать ваш пол:\n\n{preview}"
                
                await interaction.response.send_message(
                    embed=embed,
                    view=GenderRoleView(),
                    ephemeral=True
                )
                
        except Exception as e:
            print(f"Ошибка при обработке кнопки: {e}")
            await interaction.response.send_message(
                "Произошла ошибка. Пожалуйста, обратитесь к администрации.",
                ephemeral=True
            )

class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        with open("data/config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def save_config(self) -> None:
        with open("data/config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, indent=4, allow_unicode=True)

    @commands.command(name="aeroles")
    @commands.has_permissions(administrator=True)
    async def send_roles(self, ctx):
        """Отправляет панель выбора ролей (только для администраторов)"""
        # Удаляем команду
        await ctx.message.delete()
        
        embed = Embed(
            title="👑 Выбор ролей",
            description="Нажмите на соответствующую кнопку, чтобы выбрать роль:\n\n"
                      f"{Emojis.DOT} **Цветные роли** - изменить цвет вашего никнейма\n"
                      f"{Emojis.DOT} **Гендерные роли** - указать ваш пол",
            color="DEFAULT"
        )
        
        await ctx.send(
            embed=embed,
            view=RoleSelectView()
        )

    @send_roles.error
    async def send_roles_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = Embed(
                title="❌ Ошибка",
                description="У вас нет прав администратора для использования этой команды",
                color=0xe74c3c
            )
            await ctx.send(embed=embed, delete_after=5)

async def setup(bot):
    await bot.add_cog(Roles(bot)) 