from Niludetsu import Embed
from Niludetsu.locale import _
import asyncio, discord

from typing import Dict, Any

class RewardSystem:
    """Система наград"""

    REWARDS = {
        "ad_500": {
            "name": "📢 Реклама с @here",
            "description": "Реклама вашего сервера в канале партнёрств с пингом @here",
            "cost": 500,
            "type": "advertisement"
        }
    }

    def __init__(self, bot, partnership_manager):
        self.bot = bot
        self.pm = partnership_manager
        self.ad_channel_id = 1125546966076625038

    async def get_available_rewards(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Получает доступные награды"""
        points = await self.pm.get_user_points(user_id)
        available = {}

        for key, reward in self.REWARDS.items():
            available[key] = {
                **reward,
                "available": points >= reward["cost"],
                "missing_points": max(0, reward["cost"] - points)
            }

        return available

    async def redeem(self, user_id: str, reward_key: str, interaction: discord.Interaction) -> bool:
        """Обменивает баллы на награду"""
        t = _(guild_id=interaction.guild_id, bot=self.bot)

        if reward_key not in self.REWARDS:
            await interaction.followup.send(
                embed=Embed.error(description=t("partnership", "reward_not_found")),
                ephemeral=True
            )
            return False

        reward = self.REWARDS[reward_key]
        points = await self.pm.get_user_points(user_id)

        if points < reward["cost"]:
            await interaction.followup.send(
                embed=Embed.error(
                    description=t("partnership", "reward_insufficient_points", points=points, cost=reward['cost'])
                ),
                ephemeral=True
            )
            return False

        # Обработка рекламы
        if reward["type"] == "advertisement":
            success = await self._process_ad(user_id, interaction)

            if success:
                await self.pm.update_pm_stats(user_id, points=-reward["cost"])
                await interaction.followup.send(
                    embed=Embed.success(
                        description=t("partnership", "reward_redeemed", cost=reward['cost'], name=reward['name'])
                    ),
                    ephemeral=True
                )
                return True

        return False

    async def _process_ad(self, user_id: str, interaction: discord.Interaction) -> bool:
        """Обрабатывает награду рекламы"""
        t = _(guild_id=interaction.guild_id, bot=self.bot)
        modal = AdModal(self, t)
        await interaction.response.send_modal(modal)

        # Ждём заполнения
        timeout = 300
        start = asyncio.get_event_loop().time()

        while not modal.completed:
            await asyncio.sleep(0.5)
            if asyncio.get_event_loop().time() - start > timeout:
                return False

        # Проверяем инвайт
        try:
            invite = await self.bot.fetch_invite(modal.invite_link)
            if not invite or not invite.guild:
                await interaction.followup.send(
                    embed=Embed.error(description=t("partnership", "reward_invalid_link")),
                    ephemeral=True
                )
                return False
        except:
            await interaction.followup.send(
                embed=Embed.error(description=t("partnership", "reward_link_check_error")),
                ephemeral=True
            )
            return False

        # Создаём рекламу
        channel = self.bot.get_channel(self.ad_channel_id)
        if not channel:
            return False

        embed = discord.Embed(
            title=f"{invite.guild.name}",
            description=modal.description,
            color=discord.Color.gold()
        )

        if invite.guild.icon:
            embed.set_thumbnail(url=invite.guild.icon.url)

        embed.add_field(
            name=t("partnership", "reward_ad_info"),
            value=t("partnership", "reward_ad_members", count=invite.approximate_member_count, link=modal.invite_link),
            inline=False
        )

        user = self.bot.get_user(int(user_id))
        if user:
            embed.set_footer(
                text=t("partnership", "reward_ad_footer", name=user.display_name),
                icon_url=user.display_avatar.url
            )

        await channel.send("@here", embed=embed)
        return True

class AdModal(discord.ui.Modal, title="Создание рекламы"):
    """Модальное окно для рекламы"""

    def __init__(self, reward_system, t=None):
        title_text = t("partnership", "reward_ad_modal_title") if t else "Создание рекламы"
        super().__init__(title=title_text, timeout=300)
        self.reward_system = reward_system
        self.t = t
        self.completed = False
        self.invite_link = None
        self.description = None

        # Обновляем labels с локализацией
        if t:
            self.invite.label = t("partnership", "reward_ad_invite_label")
            self.invite.placeholder = t("partnership", "reward_ad_invite_placeholder")
            self.desc.label = t("partnership", "reward_ad_desc_label")
            self.desc.placeholder = t("partnership", "reward_ad_desc_placeholder")

    invite = discord.ui.TextInput(
        label="Ссылка-приглашение",
        placeholder="https://discord.gg/example",
        required=True,
        max_length=100
    )

    desc = discord.ui.TextInput(
        label="Описание сервера",
        placeholder="Опишите ваш сервер (50-500 символов)",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500,
        min_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        self.invite_link = self.invite.value
        self.description = self.desc.value
        self.completed = True

        t = self.t or _(guild_id=interaction.guild_id, bot=interaction.client)
        await interaction.response.send_message(
            embed=Embed.info(description=t("partnership", "reward_ad_processing")),
            ephemeral=True
        )

class AdRedeemView(discord.ui.View):
    """View с кнопкой обмена"""

    def __init__(self, reward_system, user_id: str):
        super().__init__(timeout=300)
        self.reward_system = reward_system
        self.user_id = user_id

        button = discord.ui.Button(
            label="Получить рекламу (500)",
            style=discord.ButtonStyle.success,
            custom_id="ad500"
        )
        button.callback = self.redeem
        self.add_item(button)

    async def redeem(self, interaction: discord.Interaction):
        if interaction.user.id != int(self.user_id):
            t = _(guild_id=interaction.guild_id, bot=interaction.client)
            await interaction.response.send_message(
                embed=Embed.error(description=t("partnership", "reward_ad_not_for_you")),
                ephemeral=True
            )
            return

        await self.reward_system.redeem(self.user_id, "ad_500", interaction)

async def setup(bot):
    pass
