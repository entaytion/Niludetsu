import discord
from discord.ext import commands
import random
import asyncio
from Niludetsu.utils.database import get_user, save_user
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS

class DuelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.value = None

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, emoji="⚔️")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label="Отказаться", style=discord.ButtonStyle.red, emoji="🏳️")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()

class Duel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weapons = {
            "🔫 Пистолет": {"dmg": (15, 25), "accuracy": 0.8, "crit": 0.2},
            "🗡️ Нож": {"dmg": (20, 30), "accuracy": 0.9, "crit": 0.3},
            "💣 Граната": {"dmg": (30, 40), "accuracy": 0.6, "crit": 0.15},
            "🏹 Лук": {"dmg": (25, 35), "accuracy": 0.75, "crit": 0.25},
            "⚡ Молния": {"dmg": (35, 45), "accuracy": 0.7, "crit": 0.35}
        }
        self.actions = [
            "целится в голову",
            "стреляет в упор",
            "пытается обойти с фланга",
            "делает резкий выпад",
            "готовит мощную атаку"
        ]
        self.misses = [
            "промахивается",
            "теряет равновесие",
            "спотыкается",
            "не успевает среагировать",
            "теряет прицел"
        ]

    @discord.app_commands.command(name="duel", description="Вызвать игрока на дуэль")
    @discord.app_commands.describe(
        member="Игрок, которого вы хотите вызвать на дуэль",
        bet="Сумма ставки"
    )
    async def duel(self, interaction: discord.Interaction, member: discord.Member, bet: int):
        if member.bot:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Нельзя вызвать на дуэль бота!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Нельзя вызвать на дуэль самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if bet <= 0:
            await interaction.response.send_message(
                embed=create_embed(
                    description="❌ Ставка должна быть больше 0!",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        challenger_id = str(interaction.user.id)
        opponent_id = str(member.id)

        challenger_data = get_user(challenger_id)
        opponent_data = get_user(opponent_id)

        if not challenger_data or challenger_data['balance'] < bet:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"❌ У вас недостаточно средств!\n"
                              f"Ваш баланс: {challenger_data.get('balance', 0):,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        if not opponent_data or opponent_data['balance'] < bet:
            await interaction.response.send_message(
                embed=create_embed(
                    description=f"❌ У {member.mention} недостаточно средств!\n"
                              f"Баланс противника: {opponent_data.get('balance', 0):,} {EMOJIS['MONEY']}",
                    color="RED"
                ),
                ephemeral=True
            )
            return

        view = DuelView()
        embed = create_embed(
            title="⚔️ Вызов на дуэль!",
            description=(
                f"{interaction.user.mention} вызывает {member.mention} на дуэль!\n\n"
                f"💰 Ставка: **{bet:,}** {EMOJIS['MONEY']}\n"
                "⏰ Время на принятие: 30 секунд"
            ),
            color="BLUE"
        )
        await interaction.response.send_message(embed=embed, view=view)

        await view.wait()
        if view.value is None:
            await interaction.edit_original_response(
                embed=create_embed(
                    description="❌ Время на принятие дуэли истекло!",
                    color="RED"
                ),
                view=None
            )
            return
        elif not view.value:
            await interaction.edit_original_response(
                embed=create_embed(
                    description=f"🏳️ {member.mention} отказался от дуэли!",
                    color="RED"
                ),
                view=None
            )
            return

        # Снимаем ставки с обоих игроков
        challenger_data['balance'] -= bet
        opponent_data['balance'] -= bet
        save_user(challenger_id, challenger_data)
        save_user(opponent_id, opponent_data)

        # Начинаем дуэль
        challenger_hp = 100
        opponent_hp = 100
        round_num = 1

        duel_embed = create_embed(
            title="⚔️ Дуэль началась!",
            description=(
                f"**{interaction.user.name}** vs **{member.name}**\n"
                f"💰 Ставка: **{bet:,}** {EMOJIS['MONEY']}\n\n"
                f"❤️ {interaction.user.name}: {challenger_hp} HP\n"
                f"❤️ {member.name}: {opponent_hp} HP"
            ),
            color="BLUE"
        )
        await interaction.edit_original_response(embed=duel_embed, view=None)
        await asyncio.sleep(2)

        while challenger_hp > 0 and opponent_hp > 0:
            # Выбираем оружие для каждого игрока
            challenger_weapon = random.choice(list(self.weapons.items()))
            opponent_weapon = random.choice(list(self.weapons.items()))

            # Первый игрок атакует
            if random.random() <= challenger_weapon[1]['accuracy']:
                damage = random.randint(*challenger_weapon[1]['dmg'])
                if random.random() <= challenger_weapon[1]['crit']:
                    damage *= 2
                    crit_text = "🎯 **КРИТ!** "
                else:
                    crit_text = ""
                opponent_hp -= damage
                action = random.choice(self.actions)
                result = f"{crit_text}{interaction.user.name} {action} используя {challenger_weapon[0]} и наносит **{damage}** урона!"
            else:
                result = f"{interaction.user.name} {random.choice(self.misses)} используя {challenger_weapon[0]}!"

            duel_embed.description = (
                f"**Раунд {round_num}**\n\n"
                f"{result}\n\n"
                f"❤️ {interaction.user.name}: {max(0, challenger_hp)} HP\n"
                f"❤️ {member.name}: {max(0, opponent_hp)} HP"
            )
            await interaction.edit_original_response(embed=duel_embed)
            await asyncio.sleep(2)

            if opponent_hp <= 0:
                break

            # Второй игрок атакует
            if random.random() <= opponent_weapon[1]['accuracy']:
                damage = random.randint(*opponent_weapon[1]['dmg'])
                if random.random() <= opponent_weapon[1]['crit']:
                    damage *= 2
                    crit_text = "🎯 **КРИТ!** "
                else:
                    crit_text = ""
                challenger_hp -= damage
                action = random.choice(self.actions)
                result = f"{crit_text}{member.name} {action} используя {opponent_weapon[0]} и наносит **{damage}** урона!"
            else:
                result = f"{member.name} {random.choice(self.misses)} используя {opponent_weapon[0]}!"

            duel_embed.description = (
                f"**Раунд {round_num}**\n\n"
                f"{result}\n\n"
                f"❤️ {interaction.user.name}: {max(0, challenger_hp)} HP\n"
                f"❤️ {member.name}: {max(0, opponent_hp)} HP"
            )
            await interaction.edit_original_response(embed=duel_embed)
            await asyncio.sleep(2)

            round_num += 1

        # Определяем победителя
        if challenger_hp <= 0 and opponent_hp <= 0:
            winner = None
            winner_data = None
            result_text = "🤝 **Ничья!** Оба игрока пали в бою!"
            color = "YELLOW"
        elif challenger_hp <= 0:
            winner = member
            winner_data = opponent_data
            result_text = f"🏆 Победитель: {member.mention}!"
            color = "GREEN"
        else:
            winner = interaction.user
            winner_data = challenger_data
            result_text = f"🏆 Победитель: {interaction.user.mention}!"
            color = "GREEN"

        if winner:
            winner_data['balance'] += bet * 2
            save_user(str(winner.id), winner_data)

        final_embed = create_embed(
            title="⚔️ Дуэль окончена!",
            description=(
                f"{result_text}\n\n"
                f"❤️ {interaction.user.name}: {max(0, challenger_hp)} HP\n"
                f"❤️ {member.name}: {max(0, opponent_hp)} HP\n\n"
                f"💰 Выигрыш: **{bet * 2:,}** {EMOJIS['MONEY']}"
            ),
            color=color
        )
        await interaction.edit_original_response(embed=final_embed)

async def setup(bot):
    await bot.add_cog(Duel(bot))