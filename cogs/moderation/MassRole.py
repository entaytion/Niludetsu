import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, has_admin_role, command_cooldown
import asyncio
from typing import List

class MassRole(commands.GroupCog, group_name="massrole"):
    def __init__(self, bot):
        self.bot = bot
        self.processing = False

    @app_commands.command(name="add")
    @app_commands.describe(role="Роль для выдачи", filter_type="Фильтр (all/members/bots)")
    @has_admin_role()  # Используем проверку роли админа
    @command_cooldown()
    async def massrole_add(self, interaction: discord.Interaction, role: discord.Role, filter_type: str):
        """Массовая выдача роли участникам"""
        await self._process_mass_role(interaction, role, filter_type, "add")

    @app_commands.command(name="remove") 
    @app_commands.describe(role="Роль для удаления", filter_type="Фильтр (all/members/bots)")
    @has_admin_role()  # Используем проверку роли админа
    @command_cooldown()
    async def massrole_remove(self, interaction: discord.Interaction, role: discord.Role, filter_type: str):
        """Массовое удаление роли у участников"""
        await self._process_mass_role(interaction, role, filter_type, "remove")

    async def process_members_batch(self, members: List[discord.Member], role: discord.Role, action: str, moderator: discord.Member) -> tuple:
        """Обработка группы участников"""
        success = 0
        failed = 0
        already = 0
        
        for member in members:
            try:
                if action == "add":
                    if role in member.roles:
                        already += 1
                        continue
                    await member.add_roles(role, reason=f"Массовая выдача роли модератором {moderator}")
                    success += 1
                else:
                    if role not in member.roles:
                        already += 1
                        continue
                    await member.remove_roles(role, reason=f"Массовое удаление роли модератором {moderator}")
                    success += 1
                await asyncio.sleep(0.1)  # Небольшая задержка между операциями
            except Exception as e:
                failed += 1
                print(f"Ошибка при управлении ролью для {member.id}: {e}")
                
        return success, failed, already

    async def _process_mass_role(self, interaction: discord.Interaction, role: discord.Role, filter_type: str, action: str):
        if self.processing:
            await interaction.response.send_message("❌ Уже выполняется другая массовая операция с ролями!")
            return

        try:
            self.processing = True
            
            # Проверяем позицию роли
            if role.position >= interaction.user.top_role.position and interaction.user != interaction.guild.owner:
                await interaction.response.send_message("❌ Эта роль выше или равна вашей высшей роли!")
                return

            # Определяем цель по фильтру
            filter_type = filter_type.lower()
            if filter_type == "all":
                targets = interaction.guild.members
            elif filter_type == "members":
                targets = [m for m in interaction.guild.members if not m.bot]
            elif filter_type == "bots":
                targets = [m for m in interaction.guild.members if m.bot]
            else:
                await interaction.response.send_message("❌ Неверный фильтр! Используйте: all, members или bots")
                return

            total_members = len(targets)
            if total_members == 0:
                await interaction.response.send_message("❌ Нет участников, подходящих под фильтр!")
                return

            # Отправляем начальное сообщение
            await interaction.response.send_message(
                embed=create_embed(
                    title="⏳ Обработка...",
                    description=f"Начинаю управление ролями для {total_members} участников..."
                )
            )
            status_message = await interaction.original_response()

            # Счетчики для статистики
            total_success = 0
            total_fail = 0
            total_already = 0
            processed = 0

            # Разбиваем участников на группы по 10
            batch_size = 10
            for i in range(0, len(targets), batch_size):
                batch = targets[i:i + batch_size]
                success, failed, already = await self.process_members_batch(batch, role, action, interaction.user)
                
                total_success += success
                total_fail += failed
                total_already += already
                processed += len(batch)

                # Обновляем статус каждые 5 секунд или при завершении
                if i % (batch_size * 5) == 0 or processed == total_members:
                    progress = (processed / total_members) * 100
                    progress_bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
                    
                    action_text = "выдана" if action == "add" else "удалена"
                    filter_text = {
                        "-all": "всем участникам",
                        "-members": "всем пользователям",
                        "-bots": "всем ботам"
                    }[filter_type]
                    
                    embed = create_embed(
                        title=f"📊 Управление ролью {role.name}",
                        description=(
                            f"**Прогресс:** {progress_bar} {progress:.1f}%\n"
                            f"**Обработано:** {processed}/{total_members}\n\n"
                            f"**Роль:** {role.mention}\n"
                            f"**Действие:** {action_text}\n"
                            f"**Фильтр:** {filter_text}\n\n"
                            f"**Успешно:** {total_success}\n"
                            f"**Уже было:** {total_already}\n"
                            f"**Ошибок:** {total_fail}"
                        )
                    )
                    await status_message.edit(embed=embed)
                    await asyncio.sleep(5)  # Задержка между обновлениями статуса

        except Exception as e:
            await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}")
        finally:
            self.processing = False

async def setup(bot):
    await bot.add_cog(MassRole(bot))