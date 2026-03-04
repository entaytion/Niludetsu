import discord
from discord.ext import commands
from Niludetsu import Embed
from Niludetsu.tools.Emojis import Emojis
from Niludetsu.config import SERVERS
from Niludetsu.moderation.automod.manager import AutoModManager
from Niludetsu.moderation.automod.rules import AutoModRuleType

class RuleSelect(discord.ui.Select):
    def __init__(self, rules):
        rule_emojis = {
            "invites": "📨",
            "links": "🔗",
            "spam": "🚫",
            "bad_words": "🤬",
            "repeated_text": "🔄",
            "caps_lock": "🔠",
            "custom_words": "📝"
        }

        options = [
            discord.SelectOption(
                label=AutoModRuleType(rt).name,
                value=rt,
                description=f"{Emojis.SUCCESS + ' Включено' if data['is_enabled'] else Emojis.ERROR + ' Выключено'}",
                emoji=rule_emojis.get(rt, "⚙️"),
                default=False
            ) for rt, data in rules.items()
        ]
        super().__init__(placeholder="🛡️ Выберите правило для управления", options=options)

    async def callback(self, interaction: discord.Interaction):
        view: RuleManageView = self.view
        await view.show_rule_settings(interaction, self.values[0])

class AddChannelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Добавить канал", style=discord.ButtonStyle.green, emoji="➕")

    async def callback(self, interaction: discord.Interaction):
        view: RuleManageView = self.view
        await view.show_add_channel_modal(interaction)

class RemoveChannelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Удалить канал", style=discord.ButtonStyle.red, emoji="➖")

    async def callback(self, interaction: discord.Interaction):
        view: RuleManageView = self.view
        await view.show_remove_channel_modal(interaction)

class BackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Назад", style=discord.ButtonStyle.gray, emoji="⬅️")

    async def callback(self, interaction: discord.Interaction):
        view: RuleManageView = self.view
        await view.show_main_menu(interaction)

class AddChannelModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Добавить канал в игнорируемые")
        self.channel_input = discord.ui.TextInput(
            label="ID канала или упоминание",
            placeholder="Введите ID канала или упомяните канал (#канал)",
            required=True,
            max_length=100
        )
        self.add_item(self.channel_input)

    async def on_submit(self, interaction: discord.Interaction):
        view: RuleManageView = self.view
        await view.add_channel_to_ignored(interaction, self.channel_input.value)

class RemoveChannelModal(discord.ui.Modal):
    def __init__(self, channels_list):
        super().__init__(title="Удалить канал из игнорируемых")
        self.channels_list = channels_list
        self.channel_input = discord.ui.TextInput(
            label="Номер канала для удаления",
            placeholder=f"Введите номер от 1 до {len(channels_list)} или 'все' для очистки",
            required=True,
            max_length=10
        )
        self.add_item(self.channel_input)

    async def on_submit(self, interaction: discord.Interaction):
        view: RuleManageView = self.view
        await view.remove_channel_from_ignored(interaction, self.channel_input.value)

class ToggleButton(discord.ui.Button):
    def __init__(self, enabled):
        super().__init__(
            label="Включить" if not enabled else "Выключить",
            style=discord.ButtonStyle.green if not enabled else discord.ButtonStyle.red
        )

    async def callback(self, interaction: discord.Interaction):
        view: RuleManageView = self.view
        await view.toggle_rule(interaction)

class RuleManageView(discord.ui.View):
    def __init__(self, bot, settings: AutoModManager, rules, guild):
        super().__init__(timeout=120)
        self.bot = bot
        self.settings = settings
        self.rules = rules
        self.guild = guild
        self.selected_rule = None
        self.message = None
        self.add_item(RuleSelect(self.rules))

    async def show_rule_settings(self, interaction, rule_type):
        self.clear_items()
        self.selected_rule = rule_type
        rule = self.rules[rule_type]
        self.add_item(ToggleButton(rule["is_enabled"]))
        self.add_item(AddChannelButton())
        if rule["ignored_channels"]:
            self.add_item(RemoveChannelButton())
        self.add_item(BackButton())

        ignored_channels_list = []
        for i, cid in enumerate(rule["ignored_channels"], 1):
            channel = self.guild.get_channel(int(cid))
            if channel:
                ignored_channels_list.append(f"{i}. {channel.mention}")
            else:
                ignored_channels_list.append(f"{i}. Канал удален (ID: {cid})")

        channels_text = "\n".join(ignored_channels_list) if ignored_channels_list else "Нет"

        embed = Embed(
            title=f"Управление правилом: {AutoModRuleType(rule_type).name}",
            description=f"Статус: {'Включено' if rule['is_enabled'] else 'Выключено'}\n**Игнорируемые каналы:**\n{channels_text}"
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def toggle_rule(self, interaction):
        new_state = await self.settings.toggle_rule(self.selected_rule)
        self.rules[self.selected_rule]["is_enabled"] = new_state

        listener = self.bot.get_cog("AutoModListener")
        if listener:
            listener.invalidate_cache()

        await self.show_rule_settings(interaction, self.selected_rule)

    async def show_add_channel_modal(self, interaction):
        modal = AddChannelModal()
        modal.view = self
        await interaction.response.send_modal(modal)

    async def show_remove_channel_modal(self, interaction):
        rule = self.rules[self.selected_rule]
        if not rule["ignored_channels"]:
            await interaction.response.send_message("Нет каналов для удаления!", ephemeral=True)
            return
        modal = RemoveChannelModal(rule["ignored_channels"])
        modal.view = self
        await interaction.response.send_modal(modal)

    async def add_channel_to_ignored(self, interaction, channel_input):
        try:
            channel_input = channel_input.strip()
            if channel_input.startswith('<#') and channel_input.endswith('>'):
                channel_id = int(channel_input[2:-1])
            else:
                channel_id = int(channel_input)

            channel = self.guild.get_channel(channel_id)
            if not channel:
                await interaction.response.send_message(
                    f"Канал с ID {channel_id} не найден на сервере!",
                    ephemeral=True
                )
                return

            rule = self.rules[self.selected_rule]
            channel_id_str = str(channel_id)

            if channel_id_str in rule["ignored_channels"]:
                await interaction.response.send_message(
                    f"Канал {channel.mention} уже в списке игнорируемых!",
                    ephemeral=True
                )
                return

            await self.settings.add_ignored_channel(self.selected_rule, channel_id_str)
            self.rules[self.selected_rule]["ignored_channels"].append(channel_id_str)

            listener = self.bot.get_cog("AutoModListener")
            if listener:
                listener.invalidate_cache()

            await interaction.response.send_message(
                f"Канал {channel.mention} добавлен в игнорируемые!",
                ephemeral=True
            )
            await self.update_rule_display()

        except ValueError:
            await interaction.response.send_message(
                "Неверный формат! Введите ID канала или упомяните канал.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"Ошибка: {str(e)}", ephemeral=True)

    async def remove_channel_from_ignored(self, interaction, channel_input):
        try:
            rule = self.rules[self.selected_rule]
            channel_input = channel_input.strip().lower()

            if channel_input in ['все', 'all', 'очистить', 'clear']:
                for channel_id in rule["ignored_channels"].copy():
                    await self.settings.remove_ignored_channel(self.selected_rule, channel_id)
                self.rules[self.selected_rule]["ignored_channels"] = []

                listener = self.bot.get_cog("AutoModListener")
                if listener:
                    listener.invalidate_cache()

                await interaction.response.send_message(
                    "Все каналы удалены из списка игнорируемых!",
                    ephemeral=True
                )
            else:
                index = int(channel_input) - 1
                if 0 <= index < len(rule["ignored_channels"]):
                    channel_id = rule["ignored_channels"][index]
                    channel = self.guild.get_channel(int(channel_id))
                    channel_name = channel.mention if channel else f"ID: {channel_id}"

                    await self.settings.remove_ignored_channel(self.selected_rule, channel_id)
                    self.rules[self.selected_rule]["ignored_channels"].pop(index)

                    listener = self.bot.get_cog("AutoModListener")
                    if listener:
                        listener.invalidate_cache()

                    await interaction.response.send_message(
                        f"Канал {channel_name} удален из списка игнорируемых!",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"Неверный номер! Введите номер от 1 до {len(rule['ignored_channels'])}",
                        ephemeral=True
                    )
                    return

            await self.update_rule_display()

        except ValueError:
            await interaction.response.send_message(
                "Неверный формат! Введите номер канала или 'все' для очистки.",
                ephemeral=True
            )
        except Exception as e:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"Ошибка: {str(e)}", ephemeral=True)
                else:
                    await interaction.followup.send(f"Ошибка: {str(e)}", ephemeral=True)
            except:
                pass

    async def show_main_menu(self, interaction):
        self.clear_items()
        self.selected_rule = None
        self.add_item(RuleSelect(self.rules))

        desc = "\n".join([
            f"**{AutoModRuleType(rt).name}**: {Emojis.SUCCESS + ' Включено' if data['is_enabled'] else Emojis.ERROR + ' Выключено'}"
            for rt, data in self.rules.items()
        ])
        embed = Embed(title="🛡️ Настройки автомодерации", description=desc)
        await interaction.response.edit_message(embed=embed, view=self)

    async def update_rule_display(self):
        if self.message and self.selected_rule:
            rule = self.rules[self.selected_rule]
            self.clear_items()
            self.add_item(ToggleButton(rule["is_enabled"]))
            self.add_item(AddChannelButton())
            if rule["ignored_channels"]:
                self.add_item(RemoveChannelButton())
            self.add_item(BackButton())

            ignored_channels_list = []
            for i, cid in enumerate(rule["ignored_channels"], 1):
                channel = self.guild.get_channel(int(cid))
                if channel:
                    ignored_channels_list.append(f"{i}. {channel.mention}")
                else:
                    ignored_channels_list.append(f"{i}. Канал удален (ID: {cid})")

            channels_text = "\n".join(ignored_channels_list) if ignored_channels_list else "Нет"

            embed = Embed(
                title=f"Управление правилом: {AutoModRuleType(self.selected_rule).name}",
                description=f"Статус: {'Включено' if rule['is_enabled'] else 'Выключено'}\n**Игнорируемые каналы:**\n{channels_text}"
            )

            try:
                await self.message.edit(embed=embed, view=self)
            except Exception as e:
                print(f"Ошибка обновления сообщения: {e}")

class AutoModSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = AutoModManager()

    @commands.command(name="automod")
    async def automod(self, ctx):
        if ctx.guild is None or ctx.guild.id != SERVERS["MAIN_ID"]:
            await ctx.reply("Автомодерация доступна только на основном сервере.")
            return

        rules = await self.settings.get_settings()
        desc = "\n".join([
            f"**{AutoModRuleType(rt).name}**: {Emojis.SUCCESS + ' Включено' if data['is_enabled'] else Emojis.ERROR + ' Выключено'}"
            for rt, data in rules.items()
        ])
        embed = Embed(title="🛡️ Настройки автомодерации", description=desc)
        view = RuleManageView(self.bot, self.settings, rules, ctx.guild)
        msg = await ctx.reply(embed=embed, view=view)
        view.message = msg

async def setup(bot):
    await bot.add_cog(AutoModSystem(bot))

