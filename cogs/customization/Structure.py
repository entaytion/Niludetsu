import discord
from .Views import ProfileView
from cogs.customization.Form import PositionSelect
from discord import app_commands
from discord.ext import commands
from Niludetsu import Embed, Colors, Emojis

class InfoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(InfoButton(
            label="Подача заявок",
            emoji=Emojis.ICON_FORM,
            custom_id="info_team_application"
        ))
        self.add_item(InfoButton(
            label="Мой профиль",
            emoji=Emojis.NAME,
            custom_id="info_profile"
        ))
        self.add_item(InfoButton(
            label="Правила сервера",
            emoji=Emojis.ICON_RULES,
            custom_id="info_rules"
        ))
        self.add_item(InfoButton(
            label="Навигатор",
            emoji=Emojis.NAVIGATOR,
            custom_id="info_navigator"
        ))
        self.add_item(InfoButton(
            label="Как отключить пинги?",
            emoji=Emojis.NOTIFICATION,
            custom_id="info_ping_off"
        ))

class InfoButton(discord.ui.Button):
    def __init__(self, label, emoji, custom_id):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label,
            emoji=emoji,
            custom_id=custom_id
        )

    async def callback(self, interaction: discord.Interaction):
        if self.custom_id == "info_team_application":
            position_view = discord.ui.View(timeout=None)
            position_view.add_item(PositionSelect())
            embed = discord.Embed(
                title=f"{Emojis.PIN} Вы хотите стать частью нашей команды?",
                description="- Для того, чтобы стать частью нашей команды, вам нужно будет выбрать должность, на которую хотите подать заявку. Для этого выберите должность из списка ниже:",
                color=Colors.PRIMARY
            )
            embed.set_image(url="https://entaytion.vercel.app/ae/aeWork.jpg")
            await interaction.response.send_message(
                embed=embed,
                view=position_view,
                ephemeral=True
            )
        elif self.custom_id == "info_profile":
            embed = discord.Embed(
                title=f"{Emojis.PIN} Профиль!",
                description=f"Добро пожаловать в ваш **личный профиль Æther!** ``👤``. Здесь вы можете настроить свой профиль на сервере и сделать его более персонализированным. Сделайте сервер комфортным для себя! ``✨``",
                color=Colors.PRIMARY
            )
            embed.set_image(url="https://entaytion.vercel.app/ae/aeProfile.jpg")
            view = ProfileView()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        elif self.custom_id == "info_rules":
            embeds = []

            # 1. Introduction Embed
            embed_intro = discord.Embed(
                description="> На сервере поощряется **свободное и неформальное общение,** включая **сарказм, черный юмор и дружеские подколы.** Однако, для поддержания уникальной атмосферы и комфорта всех участников, были введены **базовые правила общения.**"
            )
            embed_intro.set_author(
                name="Правила проекта Æther!",
                icon_url="https://entaytion.vercel.app/ae/aeIcon.gif"
            )
            embeds.append(embed_intro)

            # 2. Rule 1.1
            embed = discord.Embed(
                title="<:aePin:1355965668562047107>〢Пункт ``1.1``: Неадекватное поведение ",
                description="```Запрещается:\n- Беспричинное оскорбление.\n- Намеренные провокации/розжиг конфликтов.\n- Публикация материалов 18+ (NSFW/NSFL) вне специально предназначенных для этого каналов.```"
            )
            embed.add_field(
                name="> **Наказание:**",
                value="```Предупреждение + мут во всех чатах, кроме токсичного.```",
                inline=True
            )
            embed.add_field(
                name="> **Длительность:**",
                value="```Определяется администрацией сервера индивидуально, исходя из тяжести и систематичности нарушения.```",
                inline=True
            )
            embeds.append(embed)

            # 3. Rule 1.2
            embed = discord.Embed(
                title="<:aePin:1355965668562047107>〢Пункт ``1.2``: Деструктивное поведение",
                description="```Запрещается:\n- Массовый флуд или спам в текстовых и голосовых чатах.\n- Бессмысленный или чрезмерный спам-пинг участников.\n- Иные действия, способные нанести прямой ущерб репутации.\n```"
            )
            embed.add_field(
                name="> **Наказание:**",
                value="```Предупреждение + мут```",
                inline=True
            )
            embed.add_field(
                name="> **Длительность:**",
                value="```Определяется администрацией сервера индивидуально, исходя из тяжести и систематичности нарушения.```",
                inline=True
            )
            embeds.append(embed)

            # 4. Rule 1.3
            embed = discord.Embed(
                title="<:aePin:1355965668562047107>〢Пункт ``1.3``: Нарушение конфиденциальности",
                description="```Запрещается:\n- Действия, связанные с нарушением личных данных.\n- Выдача себя за другого участника или представителя администрации.\n- Обход действующих правил сервера путем создания твинков.\n- Деанонимизация участников без их явного согласия.```"
            )
            embed.add_field(
                name="> **Наказание:**",
                value="```Предупреждение + мут```",
                inline=True
            )
            embed.add_field(
                name="> **Длительность:**",
                value="```Определяется администрацией сервера индивидуально, исходя из тяжести и систематичности нарушения.```",
                inline=True
            )
            embeds.append(embed)

            # 5. Rule 1.4
            embed = discord.Embed(
                title="<:aePin:1355965668562047107>〢Пункт ``1.4``: Несанкционированная реклама",
                description="```Запрещается любая форма рекламы сторонних проектов, серверов, продуктов, услуг или личных каналов без предварительного согласования с администрацией сервера.```"
            )
            embed.add_field(
                name="> **Наказание:**",
                value="```Бан```",
                inline=True
            )
            embed.add_field(
                name="> **Длительность:**",
                value="```Перманентно```",
                inline=True
            )
            embeds.append(embed)

            # 6. Rule 1.5
            embed = discord.Embed(
                title="<:aePin:1355965668562047107>〢Пункт ``1.5``: Использование бота",
                description="```Запрещается намеренная нагрузка на бота, а также использование его уязвимостей или ошибок в работе для получения неправомерной выгоды, нарушения работы сервера или создания помех другим участникам.```"
            )
            embed.add_field(
                name="> **Наказание:**",
                value="```Ограничение к боту```",
                inline=True
            )
            embed.add_field(
                name="> **Длительность:**",
                value="```Перманентно```",
                inline=True
            )
            embeds.append(embed)

            # 7. Rule 1.6
            embed = discord.Embed(
                title="<:aePin:1355965668562047107>〢Пункт ``1.6``: Взаимодействие с командой Альянса",
                description="```Запрещается:\n- Злоупотребление предоставленными правами или превышение полномочий со стороны участников команды Альянса.\n- Публичное обсуждение действий и решений команды Альянса, а также их дискредитация в общих чатах.```"
            )
            embed.add_field(
                name="> **Наказание:**",
                value="```Снятие соответствующих полномочий/роли и мут```",
                inline=True
            )
            embed.add_field(
                name="> **Длительность:**",
                value="```От 3 до 7 дней```",
                inline=True
            )
            embeds.append(embed)

            # 8. Rule 1.7
            embed = discord.Embed(
                title="<:aePin:1355965668562047107>〢Пункт ``1.7``: Мошенничество",
                description="""Запрещается:\n- Любые виды мошенничества, в том числе попытки получить деньги, товары или услуги обманным путём.\n- Распространение ложной информации о товарах, услугах или проектах.\n- Реклама сомнительных ресурсов, включая казино, пирамиды и аналогичные проекты."""
            )
            embed.add_field(
                name="> **Наказание:**",
                value="```Бан```",
                inline=True
            )
            embed.add_field(
                name="> **Длительность:**",
                value="```Перманентно```",
                inline=True
            )
            embeds.append(embed)

            # 8. Rule 1.8
            embed = discord.Embed(
                title="<:aePin:1355965668562047107>〢Пункт ``1.8``: Использование голосовых каналов",
                description="```Запрещается:\n- Намеренно шуметь, дышать, кричать в микрофон, когда этого никто не просит.\n- Использовать скримеры/earrape звуки.```"
            )
            embed.add_field(
                name="> **Наказание:**",
                value="```Предупреждение + мут```",
                inline=True
            )
            embed.add_field(
                name="> **Длительность:**",
                value="```От 12 до 24 часов```",
                inline=True
            )
            embeds.append(embed)

            # 9. Terminology
            embed_term = discord.Embed(
                title="<:aePin:1355965668562047107>〢Терминология:",
                description="```- Перманентно — наказание, действующее без ограничения по времени до особого решения администрации.\n- Бан — ограничение доступа к большинству функций и каналов сервера, при котором аккаунт участника не блокируется полностью.\n- Флуд — чрезмерная отправка однотипных, бессмысленных или повторяющихся сообщений/символов.\n- Спам — массовая рассылка нежелательного или нерелевантного контента с целью привлечения внимания.```"
            )
            embeds.append(embed_term)

            await interaction.response.send_message(embeds=embeds, ephemeral=True)
        elif self.custom_id == "info_navigator":
            embed = discord.Embed(
                title=f"{Emojis.NAVIGATOR} Навигатор сервера",
                description="Вот структура нашего сервера. Выбирайте нужный канал и присоединяйтесь!",
                color=Colors.PRIMARY
            )
            embed.add_field(
                name="🌌 ｐｈａｓｅ 〢 ``Основная категория``",
                value="- <#1125546968517726228> - ``основной чат для всего.``\n- <#1345807206205096008> - ``форум для ваших фантазий.``\n- <#1370020760877535304> - ``мемчики сюда.``\n- <#1125546970522583070> - ``для команд ботов.``\n- <#1370021188004216893> - ``запрещёнку сюда.``",
                inline=False
            )
            embed.add_field(
                name="🌌 ｅａｒｔｈ 〢 ``Новостная категория``",
                value="- <#1125546966076625038> - ``новости нашего проекта.``\n- <#1398694100668252363> - ``оповещения об ивентах.``\n- <#1430147739609464885> - ``бесплатные игры для гоев.``",
                inline=False
            )
            embed.add_field(
                name="🌌 ｌｉｇｈｔ 〢 ``Развлекательная категория``",
                value="- <#1347917939017388253> - ``моменты, которые не забудут.``\n- <#1347163631522938962> - ``ваши фотографии лица.``\n- <#1125546993763237929> - ``идеи/предложения для деградации.``\n- <#1338872875532292206> - ``ищите себе половинку именно тут.``\n- <#1125546994975383643> - ``а тут ищите тиммейта.``",
                inline=False
            )
            embed.add_field(
                name="🌌 ｐａｉｎｔ 〢 ``Дополнительные категории``",
                value="- <#1414740540314091621> - ``доступ к личному каналу.``\n- <#1363075274018914354> - ``партнёры.``\n- <#1125546954995277834> - ``категория стаффа.``\n- <#1401632834883551378> - ``администраторский консилиум.``\n- <#1265403221577437204> - ``черновое.``",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif self.custom_id == "info_ping_off":
            embed = discord.Embed(
                title=f"{Emojis.NOTIFICATION} Как отключить пинги?",
                description=(
                    "Все участники **по умолчанию** получают уведомления, связанные с розыгрышами и новостями. Если вы хотите отключить это, выполните инструкцию, как показано на Gif."
                ),
                color=Colors.WARNING
            )
            embed.set_image(url="https://entaytion.vercel.app/ae/aeDisablePing.gif")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class Structure(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="aeinfo")
    @commands.has_permissions(administrator=True)
    async def aeinfo(self, ctx):
        """Отправляет информационное меню"""
        embed = discord.Embed(
            title="<:aeHearts:1380298517905412278> Ну ты попал... на Æther!",
            description="Мы — сообщество для всех, кто хочет быть собой. Всегда  открыты для людей из всех слоёв общества и рады принять каждого. Даже тебя! **Ты **готов к приключениям? ``😉``\n\n\n",
            color=0x1,
        )
        embed.set_image(url="https://entaytion.vercel.app/ae/aeAbout.jpg")
        embed.set_footer(
            text="Интересный факт: наше название не только АЕ, еще и ЪЭ!",
            icon_url="https://cdn.discordapp.com/emojis/1375868822418100424.webp?size=160"
        )
        view = InfoView()
        await ctx.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_ready(self):
        """Регистрируем view для persistent interactions"""
        self.bot.add_view(InfoView())
        self.bot.add_view(ProfileView())

    @aeinfo.error
    async def aeinfo_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("У вас недостаточно прав для использования этой команды.")

async def setup(bot):
    await bot.add_cog(Structure(bot)) 
