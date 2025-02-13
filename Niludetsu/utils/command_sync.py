import yaml, hashlib, discord
from typing import Dict, List, Any
from discord.ext import commands

class CommandSync:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.command_hashes = self.load_command_hashes()
        
    def load_command_hashes(self) -> Dict[str, str]:
        """Загружает хеши команд из файла"""
        try:
            with open('data/hash/hash.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    def save_command_hashes(self, hashes: Dict[str, str]) -> None:
        """Сохраняет хеши команд в файл"""
        with open('data/hash/hash.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(hashes, f, default_flow_style=False, allow_unicode=True)

    def get_command_hash(self, command: discord.app_commands.Command) -> str:
        """Создает стабильный хеш команды на основе её свойств"""
        command_data = [
            command.name,
            command.description,
        ]
        
        # Обработка параметров
        if hasattr(command, 'parameters'):
            params = []
            for param in command.parameters:
                params.append((param.name, str(param.type), getattr(param, 'description', '')))
            command_data.append(str(sorted(params)))
        
        # Обработка choices
        if hasattr(command, 'choices'):
            command_data.append(str(sorted([choice.name for choice in command.choices])))
        
        # Обработка permissions
        if hasattr(command, 'default_permissions'):
            command_data.append(str(command.default_permissions))
        
        return hashlib.md5(str(command_data).encode()).hexdigest()

    async def sync_commands(self) -> None:
        """Синхронизирует только измененные команды"""
        try:
            # Получаем текущие команды и их хеши
            current_commands = {cmd.name: self.get_command_hash(cmd) for cmd in self.bot.tree.get_commands()}

            # Определяем, какие команды изменились или новые
            commands_to_sync = []
            for name, hash_value in current_commands.items():
                if name not in self.command_hashes or self.command_hashes[name] != hash_value:
                    commands_to_sync.append(name)
                    self.command_hashes[name] = hash_value

            # Удаляем хеши для удаленных команд
            removed_commands = []
            for name in list(self.command_hashes.keys()):
                if name not in current_commands:
                    del self.command_hashes[name]
                    removed_commands.append(name)

            # Синхронизируем измененные команды
            if commands_to_sync or removed_commands:
                print(f"🔄 Синхронизация измененных команд: {commands_to_sync}")
                await self.bot.tree.sync()
                self.save_command_hashes(self.command_hashes)
                print(f"✅ Синхронизация завершена. Изменено: {len(commands_to_sync)} | Удалено: {len(removed_commands)}")
            else:
                print("✅ Все команды актуальны, синхронизация не требуется.")

        except Exception as e:
            print(f"❌ Ошибка при синхронизации команд: {e}") 