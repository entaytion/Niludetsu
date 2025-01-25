import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from typing import Optional
from utils import create_embed, EMOJIS, get_user, save_user

class Duel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_duels = {}

    @app_commands.command(name="duel", description="Вызвать пользователя на дуэль")
    @app_commands.describe(
        opponent="Пользователь, которого вы вызываете на дуэль",
        bet="Сумма ставки (минимум 100)"
    )
    async def duel(self, interaction: discord.Interaction, opponent: discord.Member, bet: int):
        # Проверки
        if bet < 100:
            await interaction.response.send_message(f"{EMOJIS['ERROR']} Минимальная ставка: 100 монет!", ephemeral=True)
            return

        if opponent.bot:
            await interaction.response.send_message(f"{EMOJIS['ERROR']} Вы не можете вызвать бота на дуэль!", ephemeral=True)
            return

        if opponent.id == interaction.user.id:
            await interaction.response.send_message(f"{EMOJIS['ERROR']} Вы не можете вызвать себя на дуэль!", ephemeral=True)
            return

        if interaction.user.id in self.active_duels or opponent.id in self.active_duels:
            await interaction.response.send_message(f"{EMOJIS['ERROR']} Один из участников уже участвует в дуэли!", ephemeral=True)
            return

        # Проверка балансов
        challenger_data = get_user(interaction.user.id)
        opponent_data = get_user(opponent.id)

        challenger_balance = challenger_data["balance"]
        opponent_balance = opponent_data["balance"]

        if challenger_balance < bet:
            await interaction.response.send_message(f"{EMOJIS['ERROR']} У вас недостаточно монет! Ваш баланс: {challenger_balance}", ephemeral=True)
            return

        if opponent_balance < bet:
            await interaction.response.send_message(f"{EMOJIS['ERROR']} У оппонента недостаточно монет! Баланс оппонента: {opponent_balance}", ephemeral=True)
            return

        # Создаем эмбед для вызова
        embed = create_embed(
            title="⚔️ Вызов на дуэль!",
            description=f"{interaction.user.mention} вызывает {opponent.mention} на дуэль!\n"
                       f"Ставка: **{bet}** монет\n\n"
                       f"У вас есть 30 секунд, чтобы принять или отклонить вызов."
        )

        # Создаем кнопки
        class DuelButtons(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.value = None

            @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, emoji="⚔️")
            async def accept(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != opponent.id:
                    await button_interaction.response.send_message(f"{EMOJIS['ERROR']} Только {opponent.mention} может принять этот вызов!", ephemeral=True)
                    return
                self.value = True
                for item in self.children:
                    item.disabled = True
                await button_interaction.response.edit_message(view=self)
                self.stop()

            @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, emoji="❌")
            async def decline(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                if button_interaction.user.id != opponent.id:
                    await button_interaction.response.send_message(f"{EMOJIS['ERROR']} Только {opponent.mention} может отклонить этот вызов!", ephemeral=True)
                    return
                self.value = False
                for item in self.children:
                    item.disabled = True
                await button_interaction.response.edit_message(view=self)
                self.stop()

        view = DuelButtons()
        await interaction.response.send_message(embed=embed, view=view)

        # Ждем ответ
        await view.wait()

        if view.value is None:
            await interaction.edit_original_response(
                embed=create_embed(title="⚔️ Дуэль отменена", description="Время на принятие вызова истекло."),
                view=None
            )
            return

        if not view.value:
            await interaction.edit_original_response(
                embed=create_embed(title="⚔️ Дуэль отменена", description=f"{opponent.mention} отклонил(а) вызов."),
                view=None
            )
            return

        # Начинаем дуэль
        self.active_duels[interaction.user.id] = True
        self.active_duels[opponent.id] = True

        duel_embed = create_embed(title="⚔️ Дуэль начинается!", description="Подготовка к битве...")
        await interaction.edit_original_response(embed=duel_embed, view=None)
        await asyncio.sleep(2)

        # Симуляция дуэли
        hp_challenger = 100
        hp_opponent = 100
        round_num = 1

        while hp_challenger > 0 and hp_opponent > 0:
            damage_challenger = random.randint(15, 25)
            damage_opponent = random.randint(15, 25)

            hp_opponent -= damage_challenger
            hp_challenger -= damage_opponent

            duel_embed = create_embed(
                title=f"⚔️ Дуэль - Раунд {round_num}",
                description=f"{interaction.user.mention} ⚔️ {opponent.mention}\n\n"
                           f"**{interaction.user.name}**\n"
                           f"❤️ HP: {max(0, hp_challenger)}/100\n"
                           f"⚔️ Удар: -{damage_opponent}\n\n"
                           f"**{opponent.name}**\n"
                           f"❤️ HP: {max(0, hp_opponent)}/100\n"
                           f"⚔️ Удар: -{damage_challenger}"
            )
            await interaction.edit_original_response(embed=duel_embed)
            await asyncio.sleep(2)
            round_num += 1

        # Определяем победителя
        if hp_challenger > hp_opponent:
            winner = interaction.user
            loser = opponent
        else:
            winner = opponent
            loser = interaction.user

        # Обновляем балансы
        winner_data = get_user(winner.id)
        loser_data = get_user(loser.id)

        winner_data["balance"] += bet
        loser_data["balance"] -= bet

        save_user(winner.id, winner_data)
        save_user(loser.id, loser_data)

        # Финальное сообщение
        final_embed = create_embed(
            title="🏆 Дуэль завершена!",
            description=f"**Победитель:** {winner.mention}\n"
                       f"**Проиграл:** {loser.mention}\n\n"
                       f"**Награда:** {bet} монет\n"
                       f"**Новый баланс победителя:** {winner_data['balance']} монет"
        )
        await interaction.edit_original_response(embed=final_embed)

        # Очищаем активные дуэли
        del self.active_duels[interaction.user.id]
        del self.active_duels[opponent.id]

async def setup(bot):
    await bot.add_cog(Duel(bot))