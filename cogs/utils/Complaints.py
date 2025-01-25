import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
import json
import asyncio
from utils import create_embed, EMOJIS

class ComplaintButton(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        
    @discord.ui.button(label="Отправить жалобу", style=discord.ButtonStyle.red, emoji="⚠️", custom_id="submit_complaint")
    async def submit_complaint(self, interaction: discord.Interaction, button: Button):
        modal = ComplaintModal()
        await interaction.response.send_modal(modal)

class ComplaintModal(Modal, title="⚠️ Отправить жалобу"):
    user = TextInput(
        label="Нарушитель",
        placeholder="ID пользователя или @упоминание",
        style=discord.TextStyle.short,
        required=True
    )
    
    reason = TextInput(
        label="Причина",
        placeholder="Какое правило было нарушено?",
        style=discord.TextStyle.paragraph,
        required=True
    )
    
    proof = TextInput(
        label="Доказательства",
        placeholder="Ссылки на скриншоты/сообщения или напишите 'файл' для прикрепления файла",
        style=discord.TextStyle.paragraph,
        required=False
    )
    
    additional = TextInput(
        label="Дополнительная информация",
        placeholder="Любые дополнительные детали",
        style=discord.TextStyle.paragraph,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        complaints_cog = interaction.client.get_cog("Complaints")
        if complaints_cog:
            if self.proof.value.lower() == 'файл':
                await interaction.response.send_message(
                    "📎 Пожалуйста, отправьте файл доказательства в следующем сообщении (у вас есть 5 минут)",
                    ephemeral=True
                )
                
                def check(m):
                    return m.author.id == interaction.user.id and m.attachments and m.channel.id == interaction.channel.id
                
                try:
                    file_message = await interaction.client.wait_for('message', timeout=300.0, check=check)
                    await complaints_cog.handle_complaint_submit(interaction, self, file_message.attachments)
                    await file_message.delete()
                except asyncio.TimeoutError:
                    await interaction.followup.send("❌ Время загрузки файла истекло. Пожалуйста, попробуйте отправить жалобу снова.", ephemeral=True)
            else:
                await complaints_cog.handle_complaint_submit(interaction, self)

class ComplaintView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, emoji="✅", custom_id="accept_complaint")
    async def accept(self, interaction: discord.Interaction, button: Button):
        embed = interaction.message.embeds[0]
        embed.color = 0x57F287  # Зеленый цвет в HEX
        embed.title = "✅ Жалоба принята"
            
        # Получаем ID пользователя из футера
        user_id = int(embed.footer.text.split(": ")[1])
        user = interaction.client.get_user(user_id)
        
        # Отправляем уведомление пользователю
        if user:
            try:
                await user.send("✅ Ваша жалоба была **принята**!")
            except:
                pass
        
        for item in self.children:
            item.disabled = True
            
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("✅ Жалоба помечена как принятая", ephemeral=True)
        
    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, emoji="❌", custom_id="reject_complaint")
    async def reject(self, interaction: discord.Interaction, button: Button):
        embed = interaction.message.embeds[0]
        embed.color = 0xED4245  # Красный цвет в HEX
        embed.title = "❌ Жалоба отклонена"
            
        # Получаем ID пользователя из футера
        user_id = int(embed.footer.text.split(": ")[1])
        user = interaction.client.get_user(user_id)
        
        # Отправляем уведомление пользователю
        if user:
            try:
                await user.send("❌ Ваша жалоба была **отклонена**.")
            except:
                pass
        
        for item in self.children:
            item.disabled = True
            
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("❌ Жалоба помечена как отклоненная", ephemeral=True)

class Complaints(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('config/config.json', 'r') as f:
            self.config = json.load(f)
        bot.loop.create_task(self.setup_complaints_view())

    async def setup_complaints_view(self):
        await self.bot.wait_until_ready()
        if 'COMPLAINTS_CHANNEL_ID' in self.config and 'COMPLAINTS_MESSAGE_ID' in self.config:
            try:
                channel = self.bot.get_channel(int(self.config['COMPLAINTS_CHANNEL_ID']))
                if channel:
                    try:
                        message = await channel.fetch_message(int(self.config['COMPLAINTS_MESSAGE_ID']))
                        await message.edit(view=ComplaintButton(self))
                        print(f"✅ Панель жалоб загружена: {channel.name} ({channel.id})")
                    except discord.NotFound:
                        print("❌ Сообщение с панелью жалоб не найдено!")
                else:
                    print("❌ Канал для жалоб не найден!")
            except Exception as e:
                print(f"❌ Ошибка при загрузке панели жалоб: {e}")

    @app_commands.command(name="complaints", description="Настроить систему жалоб")
    @app_commands.describe(channel="ID канала для жалоб")
    @commands.has_permissions(administrator=True)
    async def complaints(self, interaction: discord.Interaction, channel: str):
        """Настройка системы жалоб"""
        try:
            # Проверяем канал
            try:
                channel_id = int(channel)
                complaints_channel = interaction.guild.get_channel(channel_id)
                
                if not complaints_channel:
                    await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
                    return
                    
                if not isinstance(complaints_channel, discord.TextChannel):
                    await interaction.response.send_message("❌ Это должен быть текстовый канал!", ephemeral=True)
                    return
                    
            except ValueError:
                await interaction.response.send_message("❌ Неверный формат ID канала!", ephemeral=True)
                return

            # Создаем сообщение для канала жалоб
            complaints_embed = create_embed(
                title="⚠️ Отправить жалобу",
                description=(
                    "**Сообщите о нарушении правил!**\n\n"
                    "• Укажите нарушителя\n"
                    "• Опишите нарушение\n"
                    "• Предоставьте доказательства\n\n"
                    "**Нажмите на кнопку ниже, чтобы отправить жалобу!**"
                )
            )

            # Отправляем сообщение в канал
            complaints_message = await complaints_channel.send(embed=complaints_embed, view=ComplaintButton(self))
            
            # Сохраняем ID в конфиг
            self.config['COMPLAINTS_CHANNEL_ID'] = str(complaints_channel.id)
            self.config['COMPLAINTS_MESSAGE_ID'] = str(complaints_message.id)
            
            with open('config/config.json', 'w') as f:
                json.dump(self.config, f, indent=4)

            await interaction.response.send_message(
                f"✅ Система жалоб настроена в канале {complaints_channel.mention}", 
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)

    async def handle_complaint_submit(self, interaction: discord.Interaction, modal, attachments=None):
        if 'COMPLAINTS_CHANNEL_ID' not in self.config:
            await interaction.response.send_message("❌ Канал для жалоб не настроен!", ephemeral=True)
            return

        channel_id = int(self.config['COMPLAINTS_CHANNEL_ID'])
        channel = self.bot.get_channel(channel_id)
        
        if not channel:
            await interaction.response.send_message("❌ Канал для жалоб не найден!", ephemeral=True)
            return

        # Пытаемся получить пользователя по ID или упоминанию
        user_input = modal.user.value
        target_user = None
        
        if user_input.isdigit():
            target_user = interaction.guild.get_member(int(user_input))
        else:
            # Извлекаем ID из упоминания (<@123456789>)
            import re
            if match := re.match(r'<@!?(\d+)>', user_input):
                user_id = int(match.group(1))
                target_user = interaction.guild.get_member(user_id)

        user_mention = target_user.mention if target_user else f"ID: {modal.user.value}"

        proof_text = "Файл прикреплен ниже" if attachments else (modal.proof.value or 'Не предоставлено')

        embed = create_embed(
            title="⚠️ Новая жалоба",
            description=f"{EMOJIS['DOT']} **От:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                       f"{EMOJIS['DOT']} **На:** {user_mention}\n\n"
                       f"{EMOJIS['DOT']} **Причина:**\n```\n{modal.reason.value}```\n"
                       f"{EMOJIS['DOT']} **Доказательства:**\n```\n{proof_text}```\n"
                       f"{EMOJIS['DOT']} **Дополнительно:**\n```\n{modal.additional.value or 'Не указано'}```",
            footer={"text": f"ID пользователя: {interaction.user.id}"}
        )

        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        view = ComplaintView()
        
        if attachments:
            files = [await attachment.to_file() for attachment in attachments]
            await channel.send(embed=embed, view=view, files=files)
        else:
            await channel.send(embed=embed, view=view)
        
        if not modal.proof.value.lower() == 'файл':
            await interaction.response.send_message(
                "✅ Ваша жалоба отправлена! Персонал рассмотрит её в ближайшее время.", 
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "✅ Ваша жалоба с файлом отправлена! Персонал рассмотрит её в ближайшее время.", 
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Complaints(bot)) 