import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
import json
from utils import create_embed, EMOJIS

class IdeaButton(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        
    @discord.ui.button(label="Предложить идею", style=discord.ButtonStyle.green, emoji="💡", custom_id="submit_idea")
    async def submit_idea(self, interaction: discord.Interaction, button: Button):
        modal = IdeaModal()
        await interaction.response.send_modal(modal)

class IdeaModal(Modal, title="💡 Предложить идею"):
    title = TextInput(
        label="Название идеи",
        placeholder="Краткое описание вашей идеи",
        style=discord.TextStyle.short,
        required=True,
        max_length=100
    )
    
    description = TextInput(
        label="Подробное описание",
        placeholder="Опишите вашу идею подробно",
        style=discord.TextStyle.paragraph,
        required=True
    )
    
    benefits = TextInput(
        label="Преимущества",
        placeholder="Какие преимущества даст реализация вашей идеи?",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        ideas_cog = interaction.client.get_cog("Ideas")
        if ideas_cog:
            await ideas_cog.handle_idea_submit(interaction, self)

class IdeaView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, emoji="✅", custom_id="accept_idea")
    async def accept(self, interaction: discord.Interaction, button: Button):
        embed = interaction.message.embeds[0]
        embed.color = 0x57F287  # Зеленый цвет в HEX
        embed.title = "✅ Идея принята"
            
        # Получаем ID пользователя из футера
        user_id = int(embed.footer.text.split(": ")[1])
        user = interaction.client.get_user(user_id)
        
        # Отправляем уведомление пользователю
        if user:
            try:
                await user.send("✅ Ваша идея была **принята**!")
            except:
                pass
        
        for item in self.children:
            item.disabled = True
            
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("✅ Идея отмечена как принятая", ephemeral=True)
        
    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, emoji="❌", custom_id="reject_idea")
    async def reject(self, interaction: discord.Interaction, button: Button):
        embed = interaction.message.embeds[0]
        embed.color = 0xED4245  # Красный цвет в HEX
        embed.title = "❌ Идея отклонена"
            
        # Получаем ID пользователя из футера
        user_id = int(embed.footer.text.split(": ")[1])
        user = interaction.client.get_user(user_id)
        
        # Отправляем уведомление пользователю
        if user:
            try:
                await user.send("❌ Ваша идея была **отклонена**.")
            except:
                pass
        
        for item in self.children:
            item.disabled = True
            
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("❌ Идея отмечена как отклоненная", ephemeral=True)

class Ideas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('config/config.json', 'r') as f:
            self.config = json.load(f)
        bot.loop.create_task(self.setup_ideas_view())

    async def setup_ideas_view(self):
        await self.bot.wait_until_ready()
        if 'IDEAS_CHANNEL_ID' in self.config and 'IDEAS_MESSAGE_ID' in self.config:
            try:
                channel = self.bot.get_channel(int(self.config['IDEAS_CHANNEL_ID']))
                if channel:
                    try:
                        message = await channel.fetch_message(int(self.config['IDEAS_MESSAGE_ID']))
                        await message.edit(view=IdeaButton(self))
                        print(f"✅ Панель идей загружена: {channel.name} ({channel.id})")
                    except discord.NotFound:
                        print("❌ Сообщение с панелью идей не найдено!")
                else:
                    print("❌ Канал для идей не найден!")
            except Exception as e:
                print(f"❌ Ошибка при загрузке панели идей: {e}")

    @app_commands.command(name="ideas", description="Настроить систему идей")
    @app_commands.describe(channel="ID канала для идей")
    @commands.has_permissions(administrator=True)
    async def ideas(self, interaction: discord.Interaction, channel: str):
        """Настройка системы идей"""
        try:
            # Проверяем канал
            try:
                channel_id = int(channel)
                ideas_channel = interaction.guild.get_channel(channel_id)
                
                if not ideas_channel:
                    await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
                    return
                    
                if not isinstance(ideas_channel, discord.TextChannel):
                    await interaction.response.send_message("❌ Это должен быть текстовый канал!", ephemeral=True)
                    return
                    
            except ValueError:
                await interaction.response.send_message("❌ Неверный формат ID канала!", ephemeral=True)
                return

            # Создаем сообщение для канала идей
            ideas_embed = create_embed(
                title="💡 Предложить идею",
                description=(
                    "**Поделитесь своими идеями для улучшения сервера!**\n\n"
                    "• Предложите новые функции\n"
                    "• Поделитесь креативными идеями\n"
                    "• Помогите сделать сервер лучше\n\n"
                    "**Нажмите на кнопку ниже, чтобы предложить идею!**"
                )
            )

            # Отправляем сообщение в канал
            ideas_message = await ideas_channel.send(embed=ideas_embed, view=IdeaButton(self))
            
            # Сохраняем ID в конфиг
            self.config['IDEAS_CHANNEL_ID'] = str(ideas_channel.id)
            self.config['IDEAS_MESSAGE_ID'] = str(ideas_message.id)
            
            with open('config/config.json', 'w') as f:
                json.dump(self.config, f, indent=4)

            await interaction.response.send_message(
                f"✅ Система идей настроена в канале {ideas_channel.mention}", 
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)

    async def handle_idea_submit(self, interaction: discord.Interaction, modal: IdeaModal):
        if 'IDEAS_CHANNEL_ID' not in self.config:
            await interaction.response.send_message("❌ Канал для идей не настроен!", ephemeral=True)
            return

        channel_id = int(self.config['IDEAS_CHANNEL_ID'])
        channel = self.bot.get_channel(channel_id)
        
        if not channel:
            await interaction.response.send_message("❌ Канал для идей не найден!", ephemeral=True)
            return

        embed = create_embed(
            title=f"💡 Новая идея:",
            description=f"{EMOJIS['DOT']} **Автор:** {interaction.user.mention} (`{interaction.user.id}`)\n\n"
                       f"{EMOJIS['DOT']} **Описание:**\n```\n{modal.description}```\n"
                       f"{EMOJIS['DOT']} **Преимущества:**\n```\n{modal.benefits}```",
            footer={"text": f"ID пользователя: {interaction.user.id}"}
        )

        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        view = IdeaView()
        await channel.send(embed=embed, view=view)
        
        await interaction.response.send_message(
            "✅ Ваша идея отправлена! Персонал рассмотрит её в ближайшее время.", 
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Ideas(bot)) 