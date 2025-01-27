import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
import yaml
from utils import create_embed, EMOJIS
import asyncio

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

    async def _update_report_status(self, interaction: discord.Interaction, status: str, color: int, reason: str = None):
        user = interaction.client.get_user(self.user_id)
        status_emoji = "✅" if status == "принята" else "❌"

        if user:
            try:
                embed = create_embed(
                    title=f"{status_emoji} Статус вашей жалобы",
                    description=f"Ваша жалоба была **{status}**!",
                    color=color
                )
                if reason:
                    embed.add_field(name="Причина", value=reason, inline=False)
                await user.send(embed=embed)
            except discord.Forbidden:
                pass

        embed = interaction.message.embeds[0]
        embed.color = color
        embed.title = f"{status_emoji} Жалоба {status}"

        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(embed=embed, view=self)

        response_message = f"{status_emoji} Жалоба пользователя {user.mention} была {status}"
        if reason:
            response_message += f"\n**Причина:** {reason}"
        await interaction.response.send_message(response_message, ephemeral=True)

    async def _handle_accept(self, interaction: discord.Interaction, reason: str = None):
        await self._update_report_status(interaction, "принята", 0x00FF00, reason)

    async def _handle_reject(self, interaction: discord.Interaction, reason: str = None):
        await self._update_report_status(interaction, "отклонена", 0xFF0000, reason)

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: Button):
        modal = ReasonModal("Причина принятия", self._handle_accept)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, emoji="❌")
    async def reject(self, interaction: discord.Interaction, button: Button):
        modal = ReasonModal("Причина отказа", self._handle_reject)
        await interaction.response.send_modal(modal)

class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        bot.loop.create_task(self.setup_reports_view())

    async def setup_reports_view(self):
        await self.bot.wait_until_ready()
        channel_id = self.config.get('reports', {}).get('channel')
        message_id = self.config.get('reports', {}).get('message')
        
        if channel_id and message_id:
            try:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    try:
                        message = await channel.fetch_message(int(message_id))
                        embed = create_embed(
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
                        view = ReportButton()
                        await message.edit(embed=embed, view=view)
                        print(f"✅ Панель жалоб загружена: {channel.name} ({channel.id})")
                    except discord.NotFound:
                        print("❌ Сообщение с панелью жалоб не найдено!")
                else:
                    print("❌ Канал для жалоб не найден!")
            except Exception as e:
                print(f"❌ Ошибка при загрузке панели жалоб: {e}")

    async def handle_report_submit(self, interaction: discord.Interaction, user: str, reason: str, proof: str = None, additional: str = None):
        channel_id = self.config.get('reports', {}).get('channel')
        if not channel_id:
            await interaction.response.send_message("❌ Канал для жалоб не настроен!")
            return

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
                
                embed = create_embed(
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
                embed = create_embed(
                    title=f"⚠️ Новая жалоба",
                    description=(
                        f"○ **От:** {interaction.user.mention} ({interaction.user.id})\n"
                        f"○ **На:** ID: {user}\n\n"
                        f"○ **Причина:**\n{reason}\n\n"
                        f"○ **Доказательства:**\n{proof}\n\n"
                        f"○ **Дополнительно:**\n{additional if additional else 'Не указано'}\n\n"
                        f"ID пользователя: {interaction.user.id}"
                    ),
                    color=0xFF0000
                )
        else:
            embed = create_embed(
                title=f"⚠️ Новая жалоба",
                description=(
                    f"○ **От:** {interaction.user.mention} ({interaction.user.id})\n"
                    f"○ **На:** ID: {user}\n\n"
                    f"○ **Причина:**\n{reason}\n\n"
                    f"○ **Доказательства:**\n{'Не предоставлено' if not proof else proof}\n\n"
                    f"○ **Дополнительно:**\n{additional if additional else 'Не указано'}\n\n"
                    f"ID пользователя: {interaction.user.id}"
                ),
                color=0xFF0000
            )

        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        if file_attachment:
            await channel.send(file=file_attachment, embed=embed, view=ReportView(interaction.user.id, user))
        else:
            await channel.send(embed=embed, view=ReportView(interaction.user.id, user))
        
        success_embed = create_embed(
            title="✅ Жалоба отправлена",
            description="Ваша жалоба успешно отправлена! Персонал рассмотрит её в ближайшее время.",
            color=0x00FF00
        )
            
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=success_embed, ephemeral=True)

    @app_commands.command(name="reports", description="Управление панелью жалоб")
    @app_commands.describe(
        action="Действие (create/set)"
    )
    @commands.has_permissions(administrator=True)
    async def reports(self, interaction: discord.Interaction, action: str):
        action = action.lower()
        if action not in ["create", "set"]:
            await interaction.response.send_message("❌ Неверное действие! Используйте 'create' или 'set'")
            return

        try:
            if action == "create":
                embed = create_embed(
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

                view = ReportButton()
                message = await interaction.channel.send(embed=embed, view=view)
                
                if 'reports' not in self.config:
                    self.config['reports'] = {}
                self.config['reports'].update({
                    'message': str(message.id),
                    'channel': str(interaction.channel_id)
                })
                
                with open('config/config.yaml', 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, indent=4, allow_unicode=True)

                success_embed = create_embed(
                    title="✅ Панель жалоб создана",
                    description=f"Панель жалоб успешно создана в канале {interaction.channel.mention}",
                    color=0x00FF00
                )
                await interaction.response.send_message(embed=success_embed)
            else:
                if 'reports' not in self.config:
                    self.config['reports'] = {}
                self.config['reports']['channel'] = str(interaction.channel_id)
                
                with open('config/config.yaml', 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, indent=4, allow_unicode=True)
                    
                embed = create_embed(
                    title="✅ Канал для жалоб установлен",
                    description=f"Канал {interaction.channel.mention} успешно установлен для получения жалоб."
                )
                await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Произошла ошибка: {str(e)}")

async def setup(bot):
    await bot.add_cog(Reports(bot)) 