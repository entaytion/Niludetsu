import discord
from discord.ext import commands
import yaml
from typing import List, Optional

class AutoRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()
        
    def load_config(self) -> dict:
        """Загрузка конфигурации из файла"""
        try:
            with open('data/config.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Ошибка загрузки конфига: {e}")
            return {}
            
    async def get_role(self, guild: discord.Guild, role_id: str) -> Optional[discord.Role]:
        """Получение роли по ID"""
        try:
            return guild.get_role(int(role_id))
        except (ValueError, TypeError):
            print(f"Неверный ID роли: {role_id}")
            return None
        
    async def add_roles(self, member: discord.Member, role_ids: List[str]):
        """Добавление ролей пользователю по ID"""
        roles_to_add = []
        for role_id in role_ids:
            role = await self.get_role(member.guild, role_id)
            if role and role not in member.roles:
                roles_to_add.append(role)
                
        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason="Автоматическая выдача ролей")
            except discord.Forbidden:
                print(f"Недостаточно прав для выдачи ролей пользователю {member}")
            except Exception as e:
                print(f"Ошибка при выдаче ролей: {e}")
                
    async def remove_role(self, member: discord.Member, role_id: str):
        """Удаление роли у пользователя по ID"""
        role = await self.get_role(member.guild, role_id)
        if role and role in member.roles:
            try:
                await member.remove_roles(role, reason="Автоматическое удаление роли")
            except discord.Forbidden:
                print(f"Недостаточно прав для удаления роли у пользователя {member}")
            except Exception as e:
                print(f"Ошибка при удалении роли: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Обработчик входа нового участника"""
        if not self.config.get('autoroles'):
            return
            
        # Выдаем роль unverified
        unverified_role = self.config['autoroles'].get('unverified_role')
        if unverified_role:
            await self.add_roles(member, [unverified_role])
            
        # Выдаем дополнительные роли при входе
        join_roles = self.config['autoroles'].get('join_roles', [])
        if join_roles:
            await self.add_roles(member, join_roles)
            
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Обработчик сообщений для верификации"""
        if not self.config.get('autoroles'):
            return
            
        if message.author.bot or not isinstance(message.author, discord.Member):
            return
            
        # Проверяем наличие роли unverified
        unverified_role = await self.get_role(
            message.guild,
            self.config['autoroles'].get('unverified_role')
        )
        if not unverified_role or unverified_role not in message.author.roles:
            return
            
        # Удаляем роль unverified и выдаем verified
        await self.remove_role(
            message.author,
            self.config['autoroles'].get('unverified_role')
        )
        
        verified_role = self.config['autoroles'].get('verified_role')
        if verified_role:
            await self.add_roles(message.author, [verified_role])

async def setup(bot):
    await bot.add_cog(AutoRoles(bot)) 