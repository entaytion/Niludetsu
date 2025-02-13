import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.database.db import Database

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

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success, emoji="✅", custom_id="accept_idea")
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
                        title=f"{Emojis.SUCCESS} Идея принята!",
                        description="Ваша идея была принята!\nБлагодарим за вклад в развитие сервера.",
                        color="GREEN"
                    )
                )
            except:
                pass
                
            # Обновляем сообщение
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            embed.title = f"{Emojis.SUCCESS} Идея принята: {embed.title.split(':')[1]}"
            
            await interaction.message.edit(embed=embed, view=None)
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Идея обработана",
                    description=f"Идея пользователя {user.mention} была принята",
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
            
    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger, emoji="❌", custom_id="reject_idea")
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
                        title=f"{Emojis.ERROR} Идея отклонена",
                        description="Ваша идея была отклонена.",
                        color="RED"
                    )
                )
            except:
                pass
                
            # Обновляем сообщение
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.red()
            embed.title = f"{Emojis.ERROR} Идея отклонена: {embed.title.split(':')[1]}"
            
            await interaction.message.edit(embed=embed, view=None)
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.SUCCESS} Идея обработана",
                    description=f"Идея пользователя {user.mention} была отклонена",
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


class Ideas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        bot.loop.create_task(self.setup_ideas_view())

    async def setup_ideas_view(self):
        """Настройка панели идей"""
        try:
            # Получаем канал для идей
            result = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'ideas' AND key = 'channel'"
            )
            
            if not result:
                return
                
            channel_id = result['value']
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return
                
            # Создаем сообщение с панелью
            embed = Embed(
                title="💡 Предложить идею",
                description=(
                    "Нажмите на кнопку ниже, чтобы предложить свою идею для улучшения сервера.\n\n"
                    f"{Emojis.DOT} Идея должна быть конструктивной и полезной\n"
                    f"{Emojis.DOT} Опишите подробно, что вы хотите предложить\n"
                    f"{Emojis.DOT} Укажите, какую проблему решает ваша идея"
                ),
                color="BLUE"
            )
            
            message = await channel.send(embed=embed, view=IdeaButton())
            
            # Сохраняем ID сообщения
            await self.db.execute(
                """
                INSERT OR REPLACE INTO settings (category, key, value)
                VALUES ('ideas', 'message', ?)
                """,
                str(message.id)
            )
            
            return message
            
        except Exception as e:
            print(f"❌ Ошибка при настройке панели идей: {e}")
            return None

    async def handle_idea_submit(self, interaction: discord.Interaction, title: str, description: str):
        """Обработка отправки идеи"""
        try:
            # Получаем канал для идей
            channel_id = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'ideas' AND key = 'channel'"
            )
            
            if not channel_id:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Канал для идей не настроен",
                        color="RED"
                    ),
                    ephemeral=True
                )
                
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return await interaction.response.send_message(
                    embed=Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Канал для идей не найден",
                        color="RED"
                    ),
                    ephemeral=True
                )

            embed = Embed(
                title=f"💡 Новая идея: {title}",
                description=(
                    f"{Emojis.DOT} **От:** {interaction.user.mention} (`{interaction.user.id}`)\n\n"
                    f"{Emojis.DOT} **Описание:**\n```\n{description}```"
                ),
                footer={"text": f"ID пользователя: {interaction.user.id}"}
            )

            if interaction.user.avatar:
                embed.set_thumbnail(url=interaction.user.avatar.url)

            await channel.send(embed=embed, view=IdeaView(interaction.user.id))

            success_embed = Embed(
                title="✅ Идея отправлена",
                description="Ваша идея успешно отправлена!\nОжидайте ответа от администрации.",
                color="GREEN"
            )
            await interaction.response.send_message(embed=success_embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"```{str(e)}```",
                    color="RED"
                ),
                ephemeral=True
            )

    @app_commands.command(name="ideas", description="Управление панелью идей")
    @app_commands.describe(
        action="Действие (create/set)",
        message_id="ID сообщения с панелью для подачи идей",
        ideas_channel="ID канала куда будут отправляться идеи"
    )
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

        embed = Embed(
            title="💡 Предложить идею",
            description=(
                "**Есть идея по улучшению сервера?**\n"
                "Нажмите на кнопку ниже, чтобы предложить свою идею!\n\n"
                "**Требования к идеям:**\n"
                "• Идея должна быть конструктивной\n"
                "• Идея должна быть реализуемой\n"
                "• Идея не должна нарушать правила сервера\n"
                "• Одна заявка - одна идея"
            )
        )

        await message.edit(embed=embed, view=IdeaButton())
        
        # Сохраняем настройки в базу данных
        await self.db.execute(
            """
            INSERT INTO settings (category, key, value) 
            VALUES (?, ?, ?), (?, ?, ?)
            ON CONFLICT (category, key) DO UPDATE SET value = excluded.value
            """,
            'ideas', 'channel', str(ideas_channel_id),
            'ideas', 'message', str(message_id)
        )

        await interaction.response.send_message(
            f"✅ Панель идей успешно создана!\n"
            f"📝 ID сообщения: `{message_id}`\n"
            f"📨 Канал для идей: {channel.mention}"
        )

    async def _handle_set_ideas(self, interaction, ideas_channel):
        channel = await commands.TextChannelConverter().convert(interaction, ideas_channel)
        
        # Сохраняем канал в базу данных
        await self.db.execute(
            """
            INSERT INTO settings (category, key, value) 
            VALUES (?, ?, ?)
            ON CONFLICT (category, key) DO UPDATE SET value = ?
            """,
            'ideas', 'channel', str(channel.id), str(channel.id)
        )
            
        embed = Embed(
            title="✅ Канал для идей установлен",
            description=f"Канал {channel.mention} успешно установлен для получения идей."
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Ideas(bot))
