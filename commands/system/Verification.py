import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button

from Niludetsu.tools.InfoCard import InfoCard
from Niludetsu.database import database
from Niludetsu.ai.verification_service import VerificationService
from Niludetsu import Embed, Colors, Emojis, config
from Niludetsu.locale import _

MAIN_SERVER_ID = config.SERVERS["MAIN_ID"]
VERIFICATION_CHANNEL_ID = 1414934353087303720
ROLE_VERIFIED = 1126146184482930740
ROLE_UNVERIFIED = 1452231718944903249
ROLE_STAFF_MARKER = 1125344222007005188 # Роль, наличие которой запрещает менять права канала
ROLE_GIVEAWAYS = 1364498617758388245  # Розыгрыши
ROLE_NEWS = 1364498609340416040       # Новости

class VerificationModal(Modal, title="Верификация"):
    answer = TextInput(
        label="С какой целью вы присоединились?",
        style=discord.TextStyle.paragraph,
        placeholder="Например: пообщаться, найти друзей...",
        min_length=10,
        max_length=500,
        required=True
    )

    def __init__(self, cog: "Verification", mode: str, t=None):
        super().__init__()
        self.cog = cog
        self.mode = mode
        self.t = t or (lambda key, **kwargs: key)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        answer_text = self.answer.value
        user = interaction.user
        t = self.t
        
        # Cooldown check
        import time
        last_attempt = self.cog.cooldowns.get(user.id, 0)
        if time.time() - last_attempt < 86400: # 24 hours
            remaining_hours = int((86400 - (time.time() - last_attempt)) / 3600)
            await interaction.followup.send(
                f"{Emojis.ERROR} {t('cooldown', hours=remaining_hours)}", 
                ephemeral=True
            )
            return

        if self.mode == "manual":
            # Direct to manual review
            self.cog.cooldowns[user.id] = time.time()
            
            await self.cog.send_verification_log(interaction, answer_text, {}, status="manual")
            await interaction.followup.send(
                f"{Emojis.SUCCESS} {t('manual_submitted')}", 
                ephemeral=True
            )
            return

        # AI Check
        try:
            # Получаем данные о join_count из таблицы invites
            invite_record = await self.cog.db.get_row("invites", guild_id=str(user.guild.id), user_id=str(user.id))
            leave_count = invite_record.get("leave_count", 0) if invite_record else 0
            
            user_meta = {
                "id": str(user.id),
                "created_at": str(user.created_at),
                "has_avatar": user.avatar is not None,
                "leave_count": leave_count,
                "username": user.name
            }

            result = await self.cog.ai_service.score_user(user_meta, answer_text)
            self.cog.cooldowns[user.id] = time.time() # Set cooldown on attempt
            
            score = result.get("score", 0)
            decision = result.get("decision", "manual_review")

            if score >= 4:
                # Auto Verify
                await self.cog.approve_user(user)
                await self.cog.send_verification_log(interaction, answer_text, result, status="success")
                await interaction.followup.send(
                    f"{Emojis.SUCCESS} {t('auto_success')}", 
                    ephemeral=True
                )
            elif decision == "reject" or score <= 1:
                 # Reject (Soft) -> Cooldown logic?
                 await interaction.followup.send(
                     f"{Emojis.ERROR} {t('auto_failed')}", 
                     ephemeral=True
                 )
            else:
                # Manual Review (Score 2-3 or Failover)
                await self.cog.send_to_manual_review(interaction, answer_text, result)
                await interaction.followup.send(
                    f"{Emojis.WARNING} {t('manual_review')}", 
                    ephemeral=True
                )

        except Exception as e:
            print(f"[Verification] Error: {e}")
            await self.cog.send_to_manual_review(interaction, answer_text, reason=f"System Error: {e}")
            await interaction.followup.send(
                f"{Emojis.WARNING} {t('error')}", 
                ephemeral=True
            )


class VerificationView(discord.ui.LayoutView):
    def __init__(self, cog: "Verification"):
        super().__init__(timeout=None)
        self.cog = cog
        gallery = discord.ui.MediaGallery()
        gallery.add_item(media="https://entaytion.vercel.app/ae/aeVerify.jpg")

        container = discord.ui.Container(
            discord.ui.TextDisplay(
                "# Ｎ Ｕ Ｌ Ｌ Ｔ Ｈ Ｅ ． Ｒ Ｅ\n"
                "> ### **СИСТЕМА КОНТРОЛЯ БИОМАССЫ**"
            ),
            gallery,
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                "## > **ТЫ КТО ТАКОЙ?**\n"
                "Если ты зашел просто поглазеть и висеть мертвым грузом в списке участников — **пошел нахуй**.\n\n"
                "🛡️ **ПРАВИЛО nullthe.re:**\n"
                "Здесь не коллекционируют циферки. Нам плевать на количество, нам важно качество.\n"
                "Если твоя активность упадет до уровня плинтуса — мы будем кидать тебя на верификацию **каждый месяц**.\n\n"
                "**Нам не нужны ебанные боты и аморфные существа.** Докажи, что ты живой."
            ),
            discord.ui.ActionRow(
                discord.ui.Button(label="Автоматическая верификация (AI)", style=discord.ButtonStyle.blurple, custom_id="verify:auto", emoji="🤖"),
                discord.ui.Button(label="Ручная верификация", style=discord.ButtonStyle.gray, custom_id="verify:manual", emoji="👤"),
            ),
            accent_colour=discord.Colour(0x000000),
        )
        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        custom_id = interaction.data.get("custom_id")
        # Create a translation function for this interaction
        t = _(ctx=interaction)
        if custom_id == "verify:auto":
            if not self.cog.ai_enabled:
                await interaction.response.send_message(t("ai_disabled"), ephemeral=True)
                return False
            await interaction.response.send_modal(VerificationModal(self.cog, mode="auto", t=t))
            return False
        elif custom_id == "verify:manual":
            await interaction.response.send_modal(VerificationModal(self.cog, mode="manual", t=t))
            return False
        return True


class ManualReviewView(View):
    def __init__(self, cog: "Verification", user_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = user_id

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, custom_id="manual:approve")
    async def approve(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        member = guild.get_member(self.user_id)
        t = _(ctx=interaction)
        
        if not member:
            await interaction.response.send_message(t("manual_not_found"), ephemeral=True)
            self.stop()
            return

        await self.cog.approve_user(member)
        await interaction.message.delete()
        await interaction.response.send_message(t("manual_approved", user=member.mention), ephemeral=True)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, custom_id="manual:reject")
    async def reject(self, interaction: discord.Interaction, button: Button):
        t = _(ctx=interaction)
        await interaction.message.delete()
        await interaction.response.send_message(t("manual_rejected"), ephemeral=True)


class Verification(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = database
        self.ai_service = VerificationService()
        self.ai_enabled = True # Default ON
        self.cooldowns = {} # Local cooldown cache: user_id -> timestamp

    async def cog_load(self):
        self.bot.add_view(VerificationView(self))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != MAIN_SERVER_ID:
            return
        # InviteSystem/AutoRole handles initial role assignment (UNVERIFIED)

    async def approve_user(self, member: discord.Member):
        guild = member.guild
        role_verified = guild.get_role(ROLE_VERIFIED)
        role_unverified = guild.get_role(ROLE_UNVERIFIED)
        role_giveaways = guild.get_role(ROLE_GIVEAWAYS)
        role_news = guild.get_role(ROLE_NEWS)

        try:
            roles_to_add = []
            if role_verified:
                roles_to_add.append(role_verified)
            if role_giveaways:
                roles_to_add.append(role_giveaways)
            if role_news:
                roles_to_add.append(role_news)
                
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Verification Passed")
                
            if role_unverified:
                await member.remove_roles(role_unverified, reason="Verification Passed")
            
        except Exception as e:
            print(f"[Verification] Failed to update roles for {member.id}: {e}")

    async def send_verification_log(self, interaction: discord.Interaction, answer: str, ai_result: dict, status: str = "manual"):
        """
        Sends a log to the verification channel.
        status: 'success' (Auto Verified) or 'manual' (Manual Review Needed)
        """
        channel = interaction.guild.get_channel(VERIFICATION_CHANNEL_ID)
        if not channel:
            return

        user = interaction.user
        t = _(ctx=interaction)
        
        if status == "success":
            title = t("log_title_success")
            color = Colors.SUCCESS
            content = None # No pings for success
            footer_text = t("log_footer_success")
            view = None # No view needed for already approved
        else:
            title = t("log_title_manual")
            color = Colors.WARNING
            
            # Pings
            owner = interaction.guild.owner
            specific_admin = interaction.guild.get_member(config.OWNER_ID)
            pings = f"{owner.mention if owner else ''} "
            if specific_admin and specific_admin != owner:
                pings += f"{specific_admin.mention}"
            
            content = f"{pings} {t('log_ping')}"
            footer_text = t("log_footer_manual")
            view = ManualReviewView(self, user.id)

        embed = Embed(
            title=title,
            description=f"{t('log_user')}: {user.mention} (`{user.id}`)",
            color=color
        )
        embed.add_field(name=t("log_answer"), value=answer, inline=False)
        
        if ai_result and ai_result.get("score") is not None:
            score = ai_result.get("score")
            breakdown = ai_result.get("breakdown", {})
            decision = ai_result.get("decision")
            ai_reason = ai_result.get("reason")
            
            embed.add_field(name=t("log_ai_score"), value=f"{score}/5 ({decision})", inline=True)
            embed.add_field(name=t("log_ai_reason"), value=ai_reason, inline=True)
            
            # Format breakdown nicely
            breakdown_text = "\n".join([f"{k}: {v}" for k, v in breakdown.items()])
            embed.add_field(name=t("log_breakdown"), value=f"```\n{breakdown_text}\n```", inline=False)
        else:
             # Manual request or no AI context
             embed.add_field(name=t("log_manual_type"), value=t("log_manual_text"), inline=False)
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=footer_text)
        
        await channel.send(content=content, embed=embed, view=view)
        
    # Alias for backward compatibility if needed, using the new generic method
    async def send_to_manual_review(self, interaction, answer, ai_result=None, reason=None):
        # Adding reason to ai_result for display if not present
        if ai_result is None:
            ai_result = {}
        if reason:
             # If "system reason" is passed, we might want to show it. 
             # For now, let's just stick to the generic log logic or manually handle the reason field if needed.
             # But the new method relies on ai_result key 'reason'.
             ai_result['reason'] = reason
             
        await self.send_verification_log(interaction, answer, ai_result, status="manual")

    @commands.command(name="aeverify")
    @commands.is_owner()
    async def toggle_ai(self, ctx):
        t = _(ctx=ctx)
        self.ai_enabled = not self.ai_enabled
        status = "Включено" if self.ai_enabled else "Выключено"
        await ctx.send(f"AI Verification: **{status}**")

    @commands.command(name="setupverify")
    @commands.has_permissions(administrator=True)
    async def setup_verify(self, ctx):
        """Отправляет шизофреническую верификацию nullthe.re."""
        await ctx.send(view=VerificationView(self))

    @commands.command(name="roleverify")
    @commands.has_permissions(administrator=True)
    async def role_verify(self, ctx):
        """Настройка прав для роли VERIFIED."""
        t = _(ctx=ctx)
        guild = ctx.guild
        verified_role = guild.get_role(ROLE_VERIFIED)
        staff_marker_role = guild.get_role(ROLE_STAFF_MARKER)

        if not verified_role:
             await ctx.send(t("role_not_found", role_id=ROLE_VERIFIED))
             return
        
        status_msg = await ctx.send(t("role_setup_start"))
        updated_count = 0
        skipped_count = 0
        
        # Получаем все каналы (текстовые, голосовые, категории)
        all_channels = guild.channels
        
        for channel in all_channels:
            overwrites = channel.overwrites
            
            # 1. Пропускаем, если есть роль STAFF_MARKER в правах
            if staff_marker_role and staff_marker_role in overwrites:
                skipped_count += 1
                continue

            # 2. Пропускаем, если @everyone запрещено смотреть канал (приватный канал)
            # overwrites.get(guild.default_role) возвращает PermissionOverwrite или None
            everyone_perm = overwrites.get(guild.default_role)
            if everyone_perm and everyone_perm.read_messages is False:
                 skipped_count += 1
                 continue

            # 3. Устанавливаем права для role_verified
            # Проверяем, нужно ли менять (чтобы не спамить API, если уже стоит True)
            current_perm = overwrites.get(verified_role)
            if current_perm and current_perm.read_messages is True:
                continue

            try:
                # view_channel - алиас для read_messages в новых версиях, но discord.py использует read_messages в PermissionOverwrite
                await channel.set_permissions(verified_role, read_messages=True, send_messages=True, reason="Verification System Setup")
                updated_count += 1
            except Exception as e:
                print(f"[RoleVerify] Ошибка обновления {channel.name}: {e}")
        
        await status_msg.edit(content=t("role_setup_done", updated=updated_count, skipped=skipped_count))

async def setup(bot: commands.Bot):
    await bot.add_cog(Verification(bot))
