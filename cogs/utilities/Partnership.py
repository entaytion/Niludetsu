import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, EMOJIS
import yaml
import asyncio
import re
import traceback

class Partnership(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.partnership_channel_id = 1332296613988794450  # Канал для управления
        self.partnerships_output_channel_id = 1125546967217471609  # Канал для отправки партнерств
        self.owner_id = 636570363605680139
        self.partners = {}
        self.load_partners()

    def load_partners(self):
        """Загружает данные о партнерах из файла"""
        try:
            with open('config/partners.yaml', 'r', encoding='utf-8') as f:
                self.partners = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self.partners = {}

    def save_partners(self):
        """Сохраняет данные о партнерах в файл"""
        with open('config/partners.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(self.partners, f, allow_unicode=True)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Проверяет, не ушел ли партнер"""
        for msg_id, data in self.partners.items():
            if str(member.id) == str(data['user_id']):
                channel = self.bot.get_channel(self.partnership_channel_id)
                if channel:
                    owner = self.bot.get_user(self.owner_id)
                    if owner:
                        await channel.send(f"{owner.mention}, партнер {member.mention} покинул сервер!")

    async def check_invite(self, invite_code):
        """Проверяет валидность инвайт-кода"""
        try:
            invite = await self.bot.fetch_invite(invite_code)
            return True
        except (discord.NotFound, discord.HTTPException):
            return False

    async def check_partners(self):
        """Периодически проверяет валидность приглашений"""
        while True:
            for msg_id, data in list(self.partners.items()):
                invite = data.get('invite')
                if invite:
                    try:
                        await self.bot.fetch_invite(invite)
                    except (discord.NotFound, discord.HTTPException):
                        channel = self.bot.get_channel(self.partnership_channel_id)
                        if channel:
                            owner = self.bot.get_user(self.owner_id)
                            if owner:
                                user = self.bot.get_user(int(data['user_id']))
                                await channel.send(
                                    f"{owner.mention}, ссылка партнера {user.mention if user else 'Unknown'} стала недействительной!"
                                )
            await asyncio.sleep(3600)  # Проверка каждый час

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Обработчик ошибок для слеш-команд"""
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                embed=create_embed(description="❌ У вас недостаточно прав для использования этой команды!"),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=create_embed(description="❌ Произошла ошибка при выполнении команды!"),
                ephemeral=True
            )

    @app_commands.command(name="partnership", description="Присвоить партнерство пользователю")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        user="Укажите пользователя или его ID",
        message_id="ID сообщения с партнерством (необязательно)"
    )
    async def partnership(self, interaction: discord.Interaction, user: str, message_id: str = None):
        """Присваивает партнерство пользователю"""
        try:
            if interaction.channel_id != self.partnership_channel_id:
                await interaction.response.send_message(
                    embed=create_embed(description="❌ Эта команда может быть использована только в канале партнерств!"),
                    ephemeral=True
                )
                return

            # Получаем пользователя
            try:
                user_id = int(''.join(filter(str.isdigit, user)))
                member = interaction.guild.get_member(user_id)
                if not member:
                    member = await interaction.guild.fetch_member(user_id)
            except (ValueError, discord.NotFound):
                await interaction.response.send_message(
                    embed=create_embed(description="❌ Пользователь не найден!"),
                    ephemeral=True
                )
                return

            # Получаем сообщение
            try:
                if message_id:  # Если указан ID сообщения
                    referenced_message = await interaction.channel.fetch_message(int(message_id))
                else:  # Если не указан, пробуем получить из ответа
                    if not interaction.message or not interaction.message.reference:
                        await interaction.response.send_message(
                            embed=create_embed(description="❌ Укажите ID сообщения или используйте команду в ответ на сообщение!"),
                            ephemeral=True
                        )
                        return
                    referenced_message = await interaction.channel.fetch_message(interaction.message.reference.message_id)
            except (ValueError, discord.NotFound):
                await interaction.response.send_message(
                    embed=create_embed(description="❌ Сообщение не найдено!"),
                    ephemeral=True
                )
                return
            
            # Ищем ссылку в сообщении
            match = re.search(r'(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li)|discordapp\.com/invite)/[^\s]+', referenced_message.content)
            
            if not match:
                await interaction.response.send_message(
                    embed=create_embed(description="❌ В сообщении нет ссылки на Discord сервер!"),
                    ephemeral=True
                )
                return

            # Очищаем текст от ссылки и упоминаний
            discord_link = match.group(0)
            cleaned_text = referenced_message.content
            cleaned_text = cleaned_text.replace(discord_link, '').strip()
            cleaned_text = cleaned_text.replace("@everyone", "").replace("@here", "")
            for mention in referenced_message.mentions:
                cleaned_text = cleaned_text.replace(f"<@{mention.id}>", "")
                cleaned_text = cleaned_text.replace(f"<@!{mention.id}>", "")

            # Отправляем в канал партнерств
            partnerships_channel = self.bot.get_channel(self.partnerships_output_channel_id)
            if not partnerships_channel:
                await interaction.response.send_message(
                    embed=create_embed(description="❌ Не удалось найти канал для отправки партнерств!"),
                    ephemeral=True
                )
                return

            # Отправляем форматированное сообщение
            prefix = (f"Партнёр - {member.mention}\n"
                     f"Ссылка на сервер - {discord_link}\n")
            partnership_msg = await partnerships_channel.send(prefix, allowed_mentions=discord.AllowedMentions.none())
            
            if cleaned_text.strip():
                embed = create_embed(description=cleaned_text.strip())
                await partnerships_channel.send(embed=embed)

            # Сохраняем информацию
            self.partners[str(partnership_msg.id)] = {
                'user_id': str(member.id),
                'invite': discord_link
            }
            self.save_partners()

            await interaction.response.send_message(
                embed=create_embed(description=f"✅ Партнерство добавлено в канал {partnerships_channel.mention}"),
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(description="❌ Произошла ошибка!"),
                ephemeral=True
            )

    async def cog_load(self):
        """Запускает проверку партнеров при загрузке кога"""
        self.bot.loop.create_task(self.check_partners())

async def setup(bot):
    await bot.add_cog(Partnership(bot))
