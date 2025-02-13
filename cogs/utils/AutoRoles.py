import discord
from discord.ext import commands
from typing import List, Optional
from Niludetsu.database.db import Database

class AutoRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
    async def get_role(self, guild: discord.Guild, role_id: str) -> Optional[discord.Role]:
        """Получение роли по ID"""
        try:
            return guild.get_role(int(role_id))
        except (ValueError, TypeError):
            print(f"❌ Неверный ID роли: {role_id}")
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
                print(f"❌ Недостаточно прав для выдачи ролей пользователю {member}")
            except Exception as e:
                print(f"❌ Ошибка при выдаче ролей: {e}")
                
    async def remove_role(self, member: discord.Member, role_id: str):
        """Удаление роли у пользователя по ID"""
        role = await self.get_role(member.guild, role_id)
        if role and role in member.roles:
            try:
                await member.remove_roles(role, reason="Автоматическое удаление роли")
            except discord.Forbidden:
                print(f"❌ Недостаточно прав для удаления роли у пользователя {member}")
            except Exception as e:
                print(f"❌ Ошибка при удалении роли: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Обработчик входа нового участника"""
        try:
            # Получаем значения из базы данных
            # Получаем роль бота
            bot_role = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'autoroles' AND key = 'bot_role'"
            )
            
            # Получаем роли при входе
            join_roles = await self.db.fetch_one(
                "SELECT value FROM settings WHERE category = 'autoroles' AND key = 'join_roles'"
            )
            
            if member.bot and bot_role:
                await self.add_roles(member, [bot_role['value']])
                return
                
            if join_roles:
                roles_list = join_roles['value'].split(',') if isinstance(join_roles['value'], str) else [join_roles['value']]
                await self.add_roles(member, roles_list)
                
        except Exception as e:
            print(f"❌ Ошибка при выдаче ролей новому участнику: {e}")

async def setup(bot):
    await bot.add_cog(AutoRoles(bot)) 