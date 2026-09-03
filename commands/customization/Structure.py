from __future__ import annotations

import discord
from discord.ext import commands

from Niludetsu import Colors, Emojis
from .Form import PositionSelect
from .Views import ProfileButton, ProfileView

MENU_FLAG = "_structure_views_registered"
ABOUT_IMAGE_URL = "https://entaytion.vercel.app/ae/aeAbout.jpg"


def _base_embed(
    *,
    title: str,
    description: str,
    colour: int = Colors.PRIMARY,
) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=colour,
    )


def _build_panel_view(
    *,
    title: str,
    description: str,
    colour: int = Colors.PRIMARY,
    footer: str | None = None,
    media_url: str | None = None,
) -> discord.ui.LayoutView:
    view = discord.ui.LayoutView(timeout=None)
    container_items: list[discord.ui.Item] = [
        discord.ui.TextDisplay(f"### {title}"),
        discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
        discord.ui.TextDisplay(description),
    ]
    if media_url:
        container_items.extend(
            [
                discord.ui.Separator(
                    visible=False,
                    spacing=discord.SeparatorSpacing.small,
                ),
                discord.ui.MediaGallery().add_item(media=media_url),
            ]
        )
    if footer:
        container_items.extend(
            [
                discord.ui.Separator(
                    visible=False,
                    spacing=discord.SeparatorSpacing.small,
                ),
                discord.ui.TextDisplay(footer),
            ]
        )

    view.add_item(
        discord.ui.Container(
            *container_items,
            accent_colour=discord.Colour(colour),
        )
    )
    return view


def build_application_prompt() -> discord.ui.LayoutView:
    view = _build_panel_view(
        title="Подача заявок",
        description=(
            "Если хочешь стать частью команды **nullthe.re**, выбери должность ниже.\n"
            "Без пафоса: просто укажи, куда именно хочешь влезть."
        ),
        media_url="https://entaytion.vercel.app/ae/aeWork.jpg",
        footer="-# Если передумаешь, просто закрой окно и сделай вид, что этого не было.",
    )
    view.add_item(discord.ui.ActionRow(PositionSelect()))
    return view


def build_profile_prompt() -> discord.ui.LayoutView:
    view = _build_panel_view(
        title="Личный профиль",
        description=(
            "Здесь можно настроить роли, цвета и прочие мелочи,\n"
            "чтобы сервер смотрел на тебя чуть точнее."
        ),
        media_url="https://entaytion.vercel.app/ae/aeProfile.jpg",
        footer="-# Ничего сложного: нажимаешь кнопку, крутишь настройки, становишься удобнее.",
    )
    view.add_item(
        discord.ui.ActionRow(
            ProfileButton(
                label="Цвет роли",
                emoji=Emojis.ICON_PALETTE,
                custom_id="profile_color",
            ),
            ProfileButton(
                label="Гендерная роль",
                emoji=Emojis.ICON_GENDER,
                custom_id="profile_gender",
            ),
        )
    )
    view.add_item(
        discord.ui.ActionRow(
            ProfileButton(
                label="Опциональные роли",
                emoji=Emojis.ICON_NEWS,
                custom_id="profile_optional_roles",
            ),
            ProfileButton(
                label="Роль бустера",
                emoji=Emojis.ICON_BOOSTER,
                custom_id="profile_booster_role",
            ),
        )
    )
    return view


def build_rules_embeds() -> list[discord.Embed]:
    intro = _base_embed(
        title="Правила nullthe.re",
        description=(
            "Здесь нормально жить свободно, шутить криво и разговаривать без галстука.\n"
            "Но если начать ломать атмосферу, людей или сам сервер, комната ответит взаимностью."
        ),
    )
    intro.set_footer(text="Правила нужны не для красоты, а чтобы шум не превращался в мусор.")

    behaviour = _base_embed(
        title="1. Поведение",
        description=(
            "**Запрещено:**\n"
            "- беспричинно оскорблять и разгонять конфликты\n"
            "- устраивать флуд, спам и бессмысленные спам-пинги\n"
            "- кидать NSFW/NSFL не туда, где ему место\n"
            "- шуметь в голосовых, earrape'ить и намеренно мешать другим\n\n"
            "**Обычно за это:** предупреждение, мут или другие ограничения по ситуации"
        ),
    )

    safety = _base_embed(
        title="2. Безопасность и честность",
        description=(
            "**Запрещено:**\n"
            "- лезть в чужие личные данные и деанонить людей\n"
            "- выдавать себя за другого человека или за администрацию\n"
            "- обходить наказания твинками\n"
            "- мошенничать, рекламировать скам и серые схемы\n"
            "- продавливать чужие деньги, услуги или доверие через обман\n\n"
            "**Обычно за это:** жёсткие ограничения вплоть до перманентного бана"
        ),
    )

    server = _base_embed(
        title="3. Сервер, бот и команда",
        description=(
            "**Отдельно важно:**\n"
            "- не нагружай бота намеренно и не эксплуатируй его баги\n"
            "- не рекламируй сторонние проекты без согласования\n"
            "- не злоупотребляй правами, если ты в команде\n"
            "- не устраивай публичный цирк вокруг решений стаффа, если вопрос можно решить нормально\n\n"
            "**Коротко:** не ломай систему, не ломай людей и не притворяйся, что это одно и то же."
        ),
    )

    return [intro, behaviour, safety, server]


def build_ping_off_view() -> discord.ui.LayoutView:
    view = _build_panel_view(
        title="Как убрать лишние уведомления",
        description=(
            "По умолчанию роли с новостями и розыгрышами уже могут висеть на тебе.\n"
            "Если хочешь тишины, сними ненужные роли через профиль или просто отключи уведомления канала вручную."
        ),
        colour=Colors.WARNING,
        media_url="https://entaytion.vercel.app/ae/aeDisablePing.gif",
        footer="-# Иногда тишина полезнее любой активности. Даже здесь.",
    )
    return view


class StructureMenuRow(discord.ui.ActionRow):
    @discord.ui.button(
        label="Подача заявок",
        emoji=Emojis.ICON_FORM,
        style=discord.ButtonStyle.secondary,
        custom_id="structure:application",
    )
    async def application(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message(
            view=build_application_prompt(),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @discord.ui.button(
        label="Мой профиль",
        emoji=Emojis.NAME,
        style=discord.ButtonStyle.secondary,
        custom_id="structure:profile",
    )
    async def profile(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message(
            view=build_profile_prompt(),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @discord.ui.button(
        label="Правила",
        emoji=Emojis.ICON_RULES,
        style=discord.ButtonStyle.secondary,
        custom_id="structure:rules",
    )
    async def rules(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message(
            embeds=build_rules_embeds(),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    
    @discord.ui.button(
        label="Как убрать пинги?",
        emoji=Emojis.NOTIFICATION,
        style=discord.ButtonStyle.secondary,
        custom_id="structure:ping_off",
    )
    async def ping_off(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message(
            view=build_ping_off_view(),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )


class StructureMenuView(discord.ui.LayoutView):
    def __init__(self) -> None:
        super().__init__(timeout=None)

        container = discord.ui.Container(
            discord.ui.TextDisplay("### nullthe.re"),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(
                "ты уже внутри. не обещаем нормальность, зато хотя бы можно быстро понять, "
                "куда нажать и что здесь вообще происходит."
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(
                "если хочешь влиться в команду, настроить профиль или просто не потеряться "
                "в коридорах сервера, нужные двери ниже."
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            discord.ui.MediaGallery().add_item(media=ABOUT_IMAGE_URL),
            accent_colour=discord.Colour(Colors.PRIMARY),
        )

        self.add_item(container)
        self.add_item(StructureMenuRow())
        self.add_item(
            discord.ui.TextDisplay(
                "-# без пингов, без лишнего шума. только то, что действительно нужно."
            )
        )


class Structure(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        if getattr(self.bot, MENU_FLAG, False):
            return

        self.bot.add_view(StructureMenuView())
        setattr(self.bot, MENU_FLAG, True)

    @commands.command(name="aeinfo", aliases=["nullinfo", "structure"])
    @commands.has_permissions(administrator=True)
    async def aeinfo(self, ctx: commands.Context) -> None:
        await ctx.send(
            view=StructureMenuView(),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @aeinfo.error
    async def aeinfo_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "У вас недостаточно прав для использования этой команды.",
                allowed_mentions=discord.AllowedMentions.none(),
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Structure(bot))
