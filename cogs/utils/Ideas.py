import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
import yaml
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS

class ReasonModal(Modal):
    def __init__(self, title: str, callback):
        super().__init__(title=title)
        self.callback = callback

        self.reason_input = TextInput(
            label="Причина",
            placeholder="Укажите причину...",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000,
        )
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback(interaction, self.reason_input.value if self.reason_input.value else None)


class BaseButton(View):
    def __init__(self):
        super().__init__(timeout=None)


class IdeaButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Предложить идею", style=discord.ButtonStyle.primary, emoji="💡", custom_id="submit_idea")
    async def submit(self, interaction: discord.Interaction, button: Button):
        modal = IdeaModal()
        await interaction.response.send_modal(modal)


class IdeaModal(Modal):
    def __init__(self):
        super().__init__(title="Предложить идею")

        self.title_input = TextInput(
            label="Заголовок",
            placeholder="Краткое описание вашей идеи",
            style=discord.TextStyle.short,
            required=True,
            max_length=100,
        )
        self.description_input = TextInput(
            label="Описание",
            placeholder="Подробное описание вашей идеи",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000,
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        if ideas_cog := interaction.client.get_cog("Ideas"):
            await ideas_cog.handle_idea_submit(
                interaction,
                self.title_input.value,
                self.description_input.value,
            )


class IdeaView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    async def _update_idea_status(self, interaction: discord.Interaction, status: str, color: int, reason: str = None):
        user = interaction.client.get_user(self.user_id)
        status_emoji = "✅" if status == "принята" else "❌"

        if user:
            try:
                embed = create_embed(
                    title=f"{status_emoji} Статус вашей идеи",
                    description=f"Ваша идея была **{status}**!",
                    color=color,
                )
                if reason:
                    embed.add_field(name="Причина", value=reason, inline=False)
                await user.send(embed=embed)
            except discord.Forbidden:
                pass

        embed = interaction.message.embeds[0]
        embed.color = color
        embed.title = f"{status_emoji} Идея {status}"

        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(embed=embed, view=self)

        response_message = f"{status_emoji} Идея пользователя {user.mention} была {status}"
        if reason:
            response_message += f"\n**Причина:** {reason}"
        await interaction.response.send_message(response_message, ephemeral=True)

    async def _handle_accept(self, interaction: discord.Interaction, reason: str = None):
        await self._update_idea_status(interaction, "принята", 0x00FF00, reason)

    async def _handle_reject(self, interaction: discord.Interaction, reason: str = None):
        await self._update_idea_status(interaction, "отклонена", 0xFF0000, reason)

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: Button):
        modal = ReasonModal("Причина принятия", self._handle_accept)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, emoji="❌")
    async def reject(self, interaction: discord.Interaction, button: Button):
        modal = ReasonModal("Причина отказа", self._handle_reject)
        await interaction.response.send_modal(modal)


class Ideas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        bot.loop.create_task(self.setup_ideas_view())

    async def setup_ideas_view(self):
        await self.bot.wait_until_ready()
        channel_id = self.config.get('ideas', {}).get('channel')
        message_id = self.config.get('ideas', {}).get('message')
        
        if channel_id and message_id:
            try:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    try:
                        message = await channel.fetch_message(int(message_id))
                        embed = create_embed(
                            title="💡 Предложить идею",
                            description=(
                                "**Есть идея по улучшению сервера?**\n"
                                "Нажмите на кнопку ниже, чтобы предложить свою идею!\n\n"
                                "**Требования к идеям:**\n"
                                "• Идея должна быть конструктивной\n"
                                "• Идея должна быть реализуемой\n"
                                "• Идея не должна нарушать правила сервера\n"
                                "• Одна заявка - одна идея"
                            ),
                        )
                        view = IdeaButton()
                        await message.edit(embed=embed, view=view)
                        print(f"✅ Панель идей загружена: {channel.name} ({channel.id})")
                    except discord.NotFound:
                        print("❌ Сообщение с панелью идей не найдено!")
                else:
                    print("❌ Канал для идей не найден!")
            except Exception as e:
                print(f"❌ Ошибка при загрузке панели идей: {e}")

    async def handle_idea_submit(self, interaction: discord.Interaction, title: str, description: str):
        channel_id = self.config.get('ideas', {}).get('channel')
        if not channel_id:
            await interaction.response.send_message("❌ Канал для идей не настроен!")
            return

        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            await interaction.response.send_message("❌ Канал для идей не найден!")
            return

        embed = create_embed(
            title=f"💡 Новая идея: {title}",
            description=(
                f"{EMOJIS['DOT']} **От:** {interaction.user.mention} (`{interaction.user.id}`)\n\n"
                f"{EMOJIS['DOT']} **Описание:**\n```\n{description}```"
            ),
            footer={"text": f"ID пользователя: {interaction.user.id}"},
        )

        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        await channel.send(embed=embed, view=IdeaView(interaction.user.id))

        success_embed = create_embed(
            title="✅ Идея отправлена",
            description="Ваша идея успешно отправлена!\nОжидайте ответа от администрации.",
            color=0x00FF00
        )
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

    @app_commands.command(name="ideas", description="Управление панелью идей")
    @commands.has_permissions(administrator=True)
    async def ideas(self, interaction: discord.Interaction, action: str, message_id: str = None, ideas_channel: str = None):
        action = action.lower()
        if action not in ["create", "set"]:
            await interaction.response.send_message("❌ Неверное действие! Используйте 'create' или 'set'")
            return

        try:
            if action == "create":
                await self._handle_create_ideas(interaction, message_id, ideas_channel)
            else:
                await self._handle_set_ideas(interaction, ideas_channel)
        except Exception as e:
            await interaction.response.send_message(f"❌ Произошла ошибка: {str(e)}")

    async def _handle_create_ideas(self, interaction, message_id, ideas_channel):
        try:
            message = await interaction.channel.fetch_message(int(message_id))
        except (discord.NotFound, ValueError):
            await interaction.response.send_message("❌ Сообщение не найдено!")
            return

        try:
            ideas_channel_id = int(ideas_channel)
            if not (channel := self.bot.get_channel(ideas_channel_id)):
                await interaction.response.send_message("❌ Канал для идей не найден!")
                return
        except ValueError:
            await interaction.response.send_message("❌ Неверный формат ID канала!")
            return

        embed = create_embed(
            title="💡 Предложить идею",
            description=(
                "**Есть идея по улучшению сервера?**\n"
                "Нажмите на кнопку ниже, чтобы предложить свою идею!\n\n"
                "**Требования к идеям:**\n"
                "• Идея должна быть конструктивной\n"
                "• Идея должна быть реализуемой\n"
                "• Идея не должна нарушать правила сервера\n"
                "• Одна заявка - одна идея"
            ),
        )

        await message.edit(embed=embed, view=IdeaButton())

        if 'ideas' not in self.config:
            self.config['ideas'] = {}
        self.config['ideas'].update({
            'channel': str(ideas_channel_id),
            'message': str(message_id)
        })

        with open("config/config.yaml", "w", encoding='utf-8') as f:
            yaml.dump(self.config, f, indent=4, allow_unicode=True)

        success_embed = create_embed(
            title="✅ Панель идей создана",
            description=(
                f"📝 ID сообщения: `{message_id}`\n"
                f"📨 Канал для идей: {channel.mention}"
            ),
            color=0x00FF00,
        )
        await interaction.response.send_message(embed=success_embed)

    async def _handle_set_ideas(self, interaction, ideas_channel):
        channel = await commands.TextChannelConverter().convert(interaction, ideas_channel)
        
        if 'ideas' not in self.config:
            self.config['ideas'] = {}
        self.config['ideas']['channel'] = str(channel.id)

        with open("config/config.yaml", "w", encoding='utf-8') as f:
            yaml.dump(self.config, f, indent=4, allow_unicode=True)

        embed = create_embed(
            title="✅ Канал для идей установлен",
            description=f"Канал {channel.mention} успешно установлен для получения идей.",
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Ideas(bot))
