import discord
from discord import app_commands
from discord.ext import commands
import yaml
import os
from typing import Optional, Literal
from utils import create_embed, EMOJIS
import asyncio
import time

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'config/config.yaml'
        self.load_settings()
        self._command_cache = {}
        self._last_sync = 0
        self._sync_cooldown = 60  # минимальное время между синхронизациями в секундах
        self.bot.add_listener(self.on_app_command_before_invoke, 'on_app_command_before_invoke')
        
        # Создаем группу команд settings
        self.settings_group = app_commands.Group(name="settings", description="Управление настройками бота")
        
        # Регистрируем команды
        self.settings_command = self.settings_group.command(name="command", description="Управление командами")(self._settings_command)
        self.settings_group_command = self.settings_group.command(name="group", description="Управление группами команд")(self._settings_group_command)
        self.settings_list_command = self.settings_group.command(name="list", description="Показать список отключенных команд и групп")(self._settings_list)

    def load_settings(self):
        """Загружает настройки из файла"""
        if not os.path.exists(self.config_file):
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            self.settings = {
                "settings": {
                    "commands": {
                        "disabled_commands": [],
                        "disabled_groups": []
                    }
                }
            }
            self.save_settings()
        else:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                settings = config.get('settings', {})
                self.settings = settings.get('commands', {
                    "disabled_commands": [],
                    "disabled_groups": []
                })

    def save_settings(self):
        """Сохраняет настройки в файл"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Загружаем текущий конфиг
        config = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        
        # Убеждаемся, что структура существует
        if 'settings' not in config:
            config['settings'] = {}
            
        # Обновляем только секцию commands в settings
        config['settings']['commands'] = self.settings
        
        # Сохраняем обновленный конфиг
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    async def reload_commands(self):
        """Перезагружает команды бота с учетом отключенных"""
        try:
            current_time = time.time()
            
            if current_time - self._last_sync < self._sync_cooldown:
                print(f"Пропускаем синхронизацию, следующая возможна через {self._sync_cooldown - (current_time - self._last_sync):.2f} секунд")
                return True

            commands_to_add = []
            command_names = set()
            
            # Добавляем группу settings первой
            self.bot.tree.add_command(self.settings_group)
            
            for cog in self.bot.cogs.values():
                for command in cog.get_app_commands():
                    if isinstance(command, (app_commands.Command, app_commands.Group)):
                        # Пропускаем команды settings
                        if command.name == 'settings' or (hasattr(command, 'parent') and command.parent and command.parent.name == 'settings'):
                            continue

                        # Определяем группу команды
                        group_name = command.parent.name if command.parent else None
                        
                        # Пропускаем команды из отключенных групп
                        if group_name and group_name in self.settings["commands"]["disabled_groups"]:
                            continue
                            
                        # Пропускаем отключенные команды
                        if command.name in self.settings["commands"]["disabled_commands"]:
                            continue

                        # Пропускаем дубликаты
                        if command.name in command_names:
                            continue

                        commands_to_add.append(command)
                        command_names.add(command.name)

            # Проверяем, изменился ли набор команд
            current_commands = frozenset(command_names)
            if self._command_cache.get('commands') == current_commands:
                print("Набор команд не изменился, пропускаем синхронизацию")
                return True

            # Очищаем команды и добавляем все за один раз
            self.bot.tree.clear_commands(guild=None)
            
            # Затем добавляем остальные команды
            for command in commands_to_add:
                try:
                    self.bot.tree.add_command(command)
                except Exception as e:
                    print(f"Ошибка при добавлении команды {command.name}: {e}")

            # Синхронизируем с Discord только один раз в конце
            try:
                await self.bot.tree.sync()
                self._last_sync = current_time
                self._command_cache['commands'] = current_commands
                return True
            except discord.HTTPException as e:
                if e.code == 429:  # Rate limit error
                    retry_after = e.retry_after
                    print(f"Достигнут лимит запросов к API. Подождите {retry_after} секунд.")
                    # Увеличиваем cooldown если получили rate limit
                    self._sync_cooldown = max(self._sync_cooldown, retry_after + 30)
                    await asyncio.sleep(retry_after)
                    await self.bot.tree.sync()
                    self._last_sync = time.time()
                    self._command_cache['commands'] = current_commands
                    return True
                raise
            
        except Exception as e:
            print(f"Ошибка при синхронизации команд: {e}")
            return False

    async def on_app_command_before_invoke(self, interaction: discord.Interaction):
        """Проверяет, не отключена ли команда перед выполнением"""
        command_name = interaction.command.name
        group_name = interaction.command.parent.name if interaction.command.parent else None

        # Пропускаем проверку для команд settings
        if command_name == 'settings' or (group_name and group_name == 'settings'):
            return

        # Проверяем, не отключена ли группа
        if group_name and group_name in self.settings["commands"]["disabled_groups"]:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Группа команд `{group_name}` отключена!",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            raise app_commands.CommandInvokeError("Command group is disabled")

        # Проверяем, не отключена ли команда
        if command_name in self.settings["commands"]["disabled_commands"]:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Команда `{command_name}` отключена!",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            raise app_commands.CommandInvokeError("Command is disabled")

    async def is_owner(self, interaction: discord.Interaction) -> bool:
        return await self.bot.is_owner(interaction.user)

    @app_commands.describe(
        action="Действие (включить/выключить)",
        command="Имя команды или 'all' для всех команд"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Включить", value="enable"),
        app_commands.Choice(name="Выключить", value="disable")
    ])
    async def _settings_command(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        command: str
    ):
        """Включение/выключение отдельных команд"""
        if not await self.is_owner(interaction):
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Эта команда доступна только создателю бота!",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        if command.lower() == 'all':
            if action.value == 'enable':
                self.settings["commands"]["disabled_commands"] = []
                success_message = "Все команды включены!"
            else:
                all_commands = []
                for cmd in self.bot.tree.walk_commands():
                    if isinstance(cmd, app_commands.Command):
                        # Пропускаем команды settings и подкоманды
                        if cmd.name == 'settings' or (cmd.parent and cmd.parent.name == 'settings'):
                            continue
                        if not cmd.parent:  # Только основные команды
                            all_commands.append(cmd.name)
                self.settings["commands"]["disabled_commands"] = all_commands
                success_message = "Все команды отключены!"
        else:
            command = command.lower()
            cmd_exists = False
            
            # Проверяем существование команды
            for cmd in self.bot.tree.walk_commands():
                if isinstance(cmd, app_commands.Command):
                    # Пропускаем команды settings
                    if cmd.name == 'settings' or (cmd.parent and cmd.parent.name == 'settings'):
                        continue
                    if not cmd.parent and cmd.name == command:  # Только основные команды
                        cmd_exists = True
                        break

            if not cmd_exists:
                await interaction.followup.send(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} Команда `{command}` не найдена!",
                        color=0xe74c3c
                    ),
                    ephemeral=True
                )
                return

            if action.value == 'enable':
                if command in self.settings["commands"]["disabled_commands"]:
                    self.settings["commands"]["disabled_commands"].remove(command)
                success_message = f"Команда `{command}` включена!"
            else:
                if command not in self.settings["commands"]["disabled_commands"]:
                    self.settings["commands"]["disabled_commands"].append(command)
                success_message = f"Команда `{command}` отключена!"

        self.save_settings()
        
        # Перезагружаем команды
        if await self.reload_commands():
            await interaction.followup.send(
                embed=create_embed(
                    description=f"{EMOJIS['SUCCESS']} {success_message}"
                ),
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Произошла ошибка при обновлении команд!",
                    color=0xe74c3c
                ),
                ephemeral=True
            )

    @app_commands.describe(
        action="Действие (включить/выключить)",
        group="Имя группы или 'all' для всех групп"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Включить", value="enable"),
        app_commands.Choice(name="Выключить", value="disable")
    ])
    async def _settings_group_command(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        group: str
    ):
        """Включение/выключение групп команд"""
        if not await self.is_owner(interaction):
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Эта команда доступна только создателю бота!",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        if group.lower() == 'all':
            if action.value == 'enable':
                self.settings["commands"]["disabled_groups"] = []
                success_message = "Все группы команд включены!"
            else:
                all_groups = []
                for cmd in self.bot.tree.walk_commands():
                    if isinstance(cmd, app_commands.Group) and cmd.name != 'settings':
                        all_groups.append(cmd.name)
                self.settings["commands"]["disabled_groups"] = all_groups
                success_message = "Все группы команд отключены!"
        else:
            group = group.lower()
            group_exists = False
            for cmd in self.bot.tree.walk_commands():
                if isinstance(cmd, app_commands.Group) and cmd.name == group:
                    group_exists = True
                    break

            if not group_exists:
                await interaction.followup.send(
                    embed=create_embed(
                        description=f"{EMOJIS['ERROR']} Группа команд `{group}` не найдена!",
                        color=0xe74c3c
                    ),
                    ephemeral=True
                )
                return

            if action.value == 'enable':
                if group in self.settings["commands"]["disabled_groups"]:
                    self.settings["commands"]["disabled_groups"].remove(group)
                success_message = f"Группа команд `{group}` включена!"
            else:
                if group not in self.settings["commands"]["disabled_groups"]:
                    self.settings["commands"]["disabled_groups"].append(group)
                success_message = f"Группа команд `{group}` отключена!"

        self.save_settings()
        
        # Перезагружаем команды
        if await self.reload_commands():
            await interaction.followup.send(
                embed=create_embed(
                    description=f"{EMOJIS['SUCCESS']} {success_message}"
                ),
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Произошла ошибка при обновлении команд!",
                    color=0xe74c3c
                ),
                ephemeral=True
            )

    @app_commands.describe()
    async def _settings_list(
        self,
        interaction: discord.Interaction
    ):
        """Показывает список отключенных команд и групп"""
        if not await self.is_owner(interaction):
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"{EMOJIS['ERROR']} Эта команда доступна только создателю бота!",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        
        disabled_commands = self.settings["commands"]["disabled_commands"]
        disabled_groups = self.settings["commands"]["disabled_groups"]
        
        if not disabled_commands and not disabled_groups:
            await interaction.followup.send(
                embed=create_embed(
                    description="✨ Все команды и группы включены!"
                ),
                ephemeral=True
            )
            return
            
        description = ""
        if disabled_commands:
            description += "**Отключенные команды:**\n"
            description += "\n".join([f"• `/{cmd}`" for cmd in disabled_commands])
        
        if disabled_groups:
            if disabled_commands:
                description += "\n\n"
            description += "**Отключенные группы:**\n"
            description += "\n".join([f"• `{group}`" for group in disabled_groups])
            
        await interaction.followup.send(
            embed=create_embed(
                title="📋 Список отключенных команд и групп",
                description=description
            ),
            ephemeral=True
        )
        
async def setup(bot):
    await bot.add_cog(Settings(bot)) 