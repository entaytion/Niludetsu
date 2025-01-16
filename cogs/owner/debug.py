import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal
from utils import create_embed, FOOTER_SUCCESS, FOOTER_ERROR, get_user, save_user
from datetime import datetime

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="debug", description="Отладочная команда для управления данными пользователей")
    @app_commands.describe(
        action="Действие (add/set/del)",
        field="Поле для изменения",
        user="Пользователь (ID или упоминание)",
        value="Значение для установки"
    )
    async def debug(
        self,
        interaction: discord.Interaction,
        action: Literal['add', 'set', 'del'],
        field: Literal['balance', 'deposit', 'last_daily', 'last_work', 'last_rob', 'xp', 'level', 'spouse', 'marriage_date'],
        user: discord.Member,
        value: str = None
    ):
        try:
            # Проверка на владельца сервера
            if interaction.user.id != interaction.guild.owner_id:
                return await interaction.response.send_message(
                    embed=create_embed(
                        description="Эта команда доступна только владельцу сервера!",
                        footer=FOOTER_ERROR
                    ),
                    ephemeral=True
                )

            # Получаем текущие данные пользователя
            user_data = get_user(self.bot, str(user.id))
            if not user_data:
                return await interaction.response.send_message(
                    embed=create_embed(
                        description="Пользователь не найден в базе данных!",
                        footer=FOOTER_ERROR
                    ),
                    ephemeral=True
                )

            # Обработка числовых полей
            numeric_fields = ['balance', 'deposit', 'xp', 'level']
            date_fields = ['last_daily', 'last_work', 'last_rob', 'marriage_date']
            
            if field in numeric_fields:
                try:
                    current_value = user_data[field] or 0
                    if action == 'add':
                        new_value = current_value + int(value)
                    elif action == 'set':
                        new_value = int(value)
                    elif action == 'del':
                        new_value = current_value - int(value)
                    user_data[field] = max(0, new_value)  # Предотвращаем отрицательные значения
                except ValueError:
                    return await interaction.response.send_message(
                        embed=create_embed(
                            description="Некорректное числовое значение!",
                            footer=FOOTER_ERROR
                        ),
                        ephemeral=True
                    )
            
            elif field in date_fields:
                try:
                    if action in ['set', 'add']:
                        user_data[field] = value
                    elif action == 'del':
                        user_data[field] = None
                except ValueError:
                    return await interaction.response.send_message(
                        embed=create_embed(
                            description="Некорректный формат даты! Используйте YYYY-MM-DD HH:MM:SS",
                            footer=FOOTER_ERROR
                        ),
                        ephemeral=True
                    )
            
            elif field == 'spouse':
                if action == 'set':
                    user_data[field] = value
                elif action == 'del':
                    user_data[field] = None
                else:
                    return await interaction.response.send_message(
                        embed=create_embed(
                            description="Для поля spouse доступны только действия set и del",
                            footer=FOOTER_ERROR
                        ),
                        ephemeral=True
                    )

            # Сохраняем обновленные данные
            save_user(str(user.id), user_data)

            # Отправляем сообщение об успехе
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"Значение {field} для {user.mention} успешно обновлено!\n"
                              f"Новое значение: {user_data[field]}",
                    footer=FOOTER_SUCCESS
                ),
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Произошла ошибка при выполнении команды!",
                    footer=FOOTER_ERROR
                ),
                ephemeral=True
            )
            print(f"Ошибка в команде debug: {e}")

async def setup(bot):
    await bot.add_cog(Debug(bot)) 