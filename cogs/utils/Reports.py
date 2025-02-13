import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
import asyncio
from Niludetsu.database.db import Database

class ReasonModal(Modal):
    def __init__(self, title: str, callback):
        super().__init__(title=title)
        self.callback = callback

        self.reason_input = TextInput(
            label="Причина",
            placeholder="Укажите причину отказа/принятия...",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback(interaction, self.reason_input.value if self.reason_input.value else None)

class ReportButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Подать жалобу", style=discord.ButtonStyle.primary, emoji="⚠️", custom_id="submit_report")
    async def submit(self, interaction: discord.Interaction, button: Button):
        modal = ReportModal()
        await interaction.response.send_modal(modal)

class ReportModal(Modal):
    def __init__(self):
        super().__init__(title="Подать жалобу")
        
        self.user_input = TextInput(
            label="Пользователь",
            placeholder="ID или имя пользователя",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        
        self.reason_input = TextInput(
            label="Причина",
            placeholder="Опишите причину жалобы",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        
        self.proof_input = TextInput(
            label="Доказательства",
            placeholder="Напишите 'файл' чтобы прикрепить файл, или укажите ссылку",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )

        self.additional_input = TextInput(
            label="Дополнительно",
            placeholder="Дополнительная информация (необязательно)",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )
        
        self.add_item(self.user_input)
        self.add_item(self.reason_input)
        self.add_item(self.proof_input)
        self.add_item(self.additional_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        if reports_cog := interaction.client.get_cog("Reports"):
            await reports_cog.handle_report_submit(
                interaction,
                self.user_input.value,
                self.reason_input.value,
                self.proof_input.value,
                self.additional_input.value
            )

class ReportView(View):
    def __init__(self, user_id: int, reported_user: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.reported_user = reported_user

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success, emoji="✅", custom_id="accept_report")
    async def accept(self, interaction: discord.Interaction, button: Button):
        try:
            user = interaction.guild.get_member(self.user_id)
            if not user:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Пользователь не найден на сервере",
                        color="RED"
                    ),
                    ephemeral=True
                )
                
            # Отправляем уведомление пользователю
            try:
                await user.send(
                    embed=Embed(
                        title=f"{Emojis.SUCCESS} Жалоба принята!",
                        description="Ваша жалоба была принята!\nБлагодарим за помощь в поддержании порядка.",
                        color="GREEN"
                    )
                )
            except:
                pass
                
            # Обновляем сообщение
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            embed.title = f"{Emojis.SUCCESS} Жалоба принята: {embed.title.split(':')[1]}"
            
            await interaction.message.edit(embed=embed, view=None)
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Жалоба обработана",
                    description=f"Жалоба пользователя {user.mention} была принята",
                    color="GREEN"
                ),
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"```{str(e)}```",
                    color="RED"
                ),
                ephemeral=True
            )
            
    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger, emoji="❌", custom_id="reject_report")
    async def reject(self, interaction: discord.Interaction, button: Button):
        try:
            user = interaction.guild.get_member(self.user_id)
            if not user:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Пользователь не найден на сервере",
                        color="RED"
                    ),
                    ephemeral=True
                )
                
            # Отправляем уведомление пользователю
            try:
                await user.send(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Жалоба отклонена",
                        description="Ваша жалоба была отклонена.",
                        color="RED"
                    )
                )
            except:
                pass
                
            # Обновляем сообщение
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.red()
            embed.title = f"{Emojis.ERROR} Жалоба отклонена: {embed.title.split(':')[1]}"
            
            await interaction.message.edit(embed=embed, view=None)
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Жалоба обработана",
                    description=f"Жалоба пользователя {user.mention} была отклонена",
                    color="GREEN"
                ),
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"```{str(e)}```",
                    color="RED"
                ),
                ephemeral=True
            )


class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        bot.loop.create_task(self.setup_reports_view())

    async def setup_reports_view(self):
        """Настройка панели жалоб"""
        try:
            # Получаем канал для жалоб
            result = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'reports' AND key = 'channel'"
            )
            
            if not result:
                return
                
            channel_id = result['value']
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return
                
            # Создаем сообщение с панелью
            embed = Embed(
                title="⚠️ Подать жалобу",
                description=(
                    "Нажмите на кнопку ниже, чтобы подать жалобу на нарушителя.\n\n"
                    f"{Emojis.DOT} Укажите никнейм нарушителя\n"
                    f"{Emojis.DOT} Опишите суть нарушения\n"
                    f"{Emojis.DOT} Приложите доказательства (скриншоты)"
                ),
                color="BLUE"
            )
            
            message = await channel.send(embed=embed, view=ReportButton())
            
            # Сохраняем ID сообщения
            await self.db.execute(
                """
                INSERT OR REPLACE INTO settings (category, key, value)
                VALUES ('reports', 'message', ?)
                """,
                str(message.id)
            )
            
            return message
            
        except Exception as e:
            print(f"❌ Ошибка при настройке панели жалоб: {e}")
            return None

    async def handle_report_submit(self, interaction: discord.Interaction, user: str, reason: str, proof: str = None, additional: str = None):
        """Обработка отправки жалобы"""
        try:
            result = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'reports' AND key = 'channel'"
            )
                
            if not result:
                await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Канал для жалоб не настроен",
                        color="RED"
                    ),
                    ephemeral=True
                )
                return

            channel_id = result['value']
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                await interaction.response.send_message("❌ Канал для жалоб не найден!")
                return

            file_attachment = None
            if proof and proof.lower() == 'файл':
                await interaction.response.send_message("Пожалуйста, прикрепите файл-доказательство:")
                
                try:
                    file_msg = await self.bot.wait_for(
                        'message',
                        timeout=60.0,
                        check=lambda m: m.author == interaction.user and m.channel == interaction.channel and len(m.attachments) > 0
                    )
                    
                    attachment = file_msg.attachments[0]
                    file_attachment = await attachment.to_file()
                    
                    embed = Embed(
                        title=f"⚠️ Новая жалоба",
                        description=(
                            f"○ **От:** {interaction.user.mention} ({interaction.user.id})\n"
                            f"○ **На:** ID: {user}\n\n"
                            f"○ **Причина:**\n{reason}\n\n"
                            f"○ **Доказательства:**\nПрикреплённый файл\n\n"
                            f"○ **Дополнительно:**\n{additional if additional else 'Не указано'}\n\n"
                            f"ID пользователя: {interaction.user.id}"
                        ),
                        color='RED'
                    )
                    
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        embed.set_image(url=attachment.proxy_url)
                    
                    await file_msg.delete()
                    
                    await channel.send(
                        file=file_attachment,
                        embed=embed,
                        view=ReportView(interaction.user.id, user)
                    )
                except asyncio.TimeoutError:
                    proof = "Файл не был предоставлен"
                    embed = Embed(
                        title=f"⚠️ Новая жалоба",
                        description=(
                            f"○ **От:** {interaction.user.mention} ({interaction.user.id})\n"
                            f"○ **На:** ID: {user}\n\n"
                            f"○ **Причина:**\n{reason}\n\n"
                            f"○ **Доказательства:**\n{proof}\n\n"
                            f"○ **Дополнительно:**\n{additional if additional else 'Не указано'}\n\n"
                            f"ID пользователя: {interaction.user.id}"
                        ),
                        color='RED'
                    )
            else:
                embed = Embed(
                    title=f"⚠️ Новая жалоба",
                    description=(
                        f"○ **От:** {interaction.user.mention} ({interaction.user.id})\n"
                        f"○ **На:** ID: {user}\n\n"
                        f"○ **Причина:**\n{reason}\n\n"
                        f"○ **Доказательства:**\n{'Не предоставлено' if not proof else proof}\n\n"
                        f"○ **Дополнительно:**\n{additional if additional else 'Не указано'}\n\n"
                        f"ID пользователя: {interaction.user.id}"
                    ),
                    color='RED'
                )

            if interaction.user.avatar:
                embed.set_thumbnail(url=interaction.user.avatar.url)

            if file_attachment:
                await channel.send(file=file_attachment, embed=embed, view=ReportView(interaction.user.id, user))
            else:
                await channel.send(embed=embed, view=ReportView(interaction.user.id, user))
            
            success_embed = Embed(
                title="✅ Жалоба отправлена",
                description="Ваша жалоба успешно отправлена! Персонал рассмотрит её в ближайшее время.",
                color="GREEN"
            )
                
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=success_embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=success_embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"```{str(e)}```",
                    color="RED"
                ),
                ephemeral=True
            )

    @app_commands.command(name="reports", description="Управление панелью жалоб")
    @app_commands.describe(
        action="Действие (create/set)",
        message_id="ID сообщения с панелью для подачи жалоб",
        reports_channel="ID канала куда будут отправляться жалобы"
    )
    @commands.has_permissions(administrator=True)
    async def reports(self, interaction: discord.Interaction, action: str, message_id: str = None, reports_channel: str = None):
        action = action.lower()
        if action not in ["create", "set"]:
            await interaction.response.send_message("❌ Неверное действие! Используйте 'create' или 'set'")
            return

        try:
            if action == "create":
                await self._handle_create_reports(interaction, message_id, reports_channel)
            else:
                await self._handle_set_reports(interaction, reports_channel)
        except Exception as e:
            await interaction.response.send_message(f"❌ Произошла ошибка: {str(e)}")

    async def _handle_create_reports(self, interaction, message_id, reports_channel):
        try:
            message = await interaction.channel.fetch_message(int(message_id))
        except (discord.NotFound, ValueError):
            await interaction.response.send_message("❌ Сообщение не найдено!")
            return

        try:
            reports_channel_id = int(reports_channel)
            if not (channel := self.bot.get_channel(reports_channel_id)):
                await interaction.response.send_message("❌ Канал для жалоб не найден!")
                return
        except ValueError:
            await interaction.response.send_message("❌ Неверный формат ID канала!")
            return

        embed = Embed(
            title="⚠️ Подать жалобу",
            description=(
                "**Столкнулись с нарушением правил?**\n"
                "Нажмите на кнопку ниже, чтобы подать жалобу!\n\n"
                "**Требования к жалобам:**\n"
                "• Укажите пользователя и причину\n"
                "• Предоставьте доказательства\n"
                "• Жалоба должна быть обоснованной\n"
                "• Ложные жалобы наказуемы"
            )
        )

        await message.edit(embed=embed, view=ReportButton())
        
        # Сохраняем настройки в базу данных
        await self.db.execute(
            """
            INSERT INTO settings (category, key, value) 
            VALUES (?, ?, ?), (?, ?, ?)
            ON CONFLICT (category, key) DO UPDATE SET value = excluded.value
            """,
            'reports', 'channel', str(reports_channel_id),
            'reports', 'message', str(message_id)
        )

        await interaction.response.send_message(
            f"✅ Панель жалоб успешно создана!\n"
            f"📝 ID сообщения: `{message_id}`\n"
            f"📨 Канал для жалоб: {channel.mention}"
        )

    async def _handle_set_reports(self, interaction, reports_channel):
        channel = await commands.TextChannelConverter().convert(interaction, reports_channel)
        
        # Сохраняем канал в базу данных
        await self.db.execute(
            """
            INSERT INTO settings (category, key, value) 
            VALUES (?, ?, ?)
            ON CONFLICT (category, key) DO UPDATE SET value = ?
            """,
            'reports', 'channel', str(channel.id), str(channel.id)
        )
            
        embed = Embed(
            title="✅ Канал для жалоб установлен",
            description=f"Канал {channel.mention} успешно установлен для получения жалоб."
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Reports(bot)) 