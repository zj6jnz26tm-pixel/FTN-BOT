import os
import random
import time
from datetime import timedelta
from collections import defaultdict
import io
from PIL import Image, ImageOps, ImageDraw
import discord
from discord import app_commands
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class FynexBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands successfully for Fynex Bot.")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

bot = FynexBot()

AI_CHANNEL_ID = 1567709659974860860

# ==================== قواعد البيانات والمتغيرات ====================
user_balances = {}
user_xp = defaultdict(int)
user_level = defaultdict(int)
user_rep = defaultdict(int)
user_mood = defaultdict(lambda: "عادي")

server_protections = {
    "anti_links": True,
    "anti_spam": True,
    "anti_bots": False
}

# إعدادات الترحيب: {guild_id: {"channel_id": id, "message": "...", "autorole_id": id, "design": 2}}
welcome_settings = {}
admin_logs = {}
user_message_timestamps = defaultdict(list)
user_warnings = defaultdict(int)

SPAM_LIMIT = 4
TIME_WINDOW = 5.0
MAX_WARNINGS = 3

GENERAL_RESPONSES = [
    "يا هلا! أنا معك، اسأل اللي بخاطرك وأنا أخوك في روم الـ AI ✨",
    "صدقت! عاد علمنا، وش وديان السوالف اليوم في سيرفرنا؟",
    "ممم.. نقطة مهمة! شاركنا تفاصيل أكثر عشان نفيدك أكثر يا غالي.",
    "أنا حاضر وموجود طوال الوقت، تفضل اطرح سؤالك أو موضوعك!"
]


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} | Fynex Bot Online 🚀')
    if not auto_event_task.is_running():
        auto_event_task.start()


# ==================== 🌸 نظام الترحيب مع اختيار الإطارات وصورة العضو ====================
@bot.event
async def on_member_join(member: discord.Member):
    guild_id = member.guild.id
    
    # 7. إعطاء رتبة تلقائية عند الانضمام
    if guild_id in welcome_settings and "autorole_id" in welcome_settings[guild_id]:
        role_id = welcome_settings[guild_id]["autorole_id"]
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
            except:
                pass

    if guild_id not in welcome_settings:
        return
    
    data = welcome_settings[guild_id]
    channel_id = data.get("channel_id")
    custom_msg = data.get("message", "أهلاً بك يا {member} في سيرفر {server}!")

    if not channel_id:
        return

    channel = member.guild.get_channel(channel_id)
    if not channel:
        return

    formatted_msg = custom_msg.format(
        member=member.mention,
        name=member.name,
        server=member.guild.name,
        count=member.guild.member_count
    )

    try:
        avatar_asset = member.display_avatar.with_size(256)
        avatar_bytes = await avatar_asset.read()
        
        avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar_img = avatar_img.resize((140, 140))

        mask = Image.new("L", (140, 140), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 140, 140), fill=255)

        output_img = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        draw_frame = ImageDraw.Draw(output_img)
        
        # اختيار لون أو إطار حسب التصميم المحدد
        design_id = data.get("design", 2)
        if design_id == 3:
            frame_color = (138, 43, 225, 255) # بنفسجي
        elif design_id == 4:
            frame_color = (220, 20, 60, 255)  # أحمر
        elif design_id == 5:
            frame_color = (0, 206, 209, 255)  # سماوي
        else:
            frame_color = (255, 215, 0, 255)  # ذهبي افتراضي

        draw_frame.ellipse((0, 0, 160, 160), fill=frame_color)
        output_img.paste(avatar_img, (10, 10), mask=mask)

        buffer = io.BytesIO()
        output_img.save(buffer, format="PNG")
        buffer.seek(0)

        file = discord.File(buffer, filename="welcome_avatar.png")

        embed = discord.Embed(
            title=f"✨ عضو جديد (التصميم #{design_id})",
            description=formatted_msg,
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="attachment://welcome_avatar.png")
        embed.add_field(name="📊 ترتيبك بين الأعضاء", value=f"رقم العضو: #{member.guild.member_count}", inline=False)
        embed.set_footer(text=f"نورت سيرفر {member.guild.name}", icon_url=member.guild.icon.url if member.guild.icon else None)

        await channel.send(embed=embed, file=file)
    except Exception as e:
        print(f"Error in welcome event: {e}")


# ==================== 💬 الرسائل والمستويات والمزاج والسبام ====================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id

    # 1. نظام مستويات XP
    user_xp[uid] += random.randint(5, 15)
    current_xp = user_xp[uid]
    next_level_xp = (user_level[uid] + 1) * 100
    if current_xp >= next_level_xp:
        user_level[uid] += 1
        try:
            await message.channel.send(f"🎉 مبروك يا {message.author.mention}! لقد صعدت إلى المستوى **{user_level[uid]}** 🚀!")
        except:
            pass

    # 13. نظام المزاج
    mood = user_mood[uid]
    mood_prefix = ""
    if mood == "رسمي":
        mood_prefix = "نظراً لطلبك، تفضل: "
    elif mood == "حماسي":
        mood_prefix = "يا وحش! 🔥 "
    elif mood == "ساخر":
        mood_prefix = "ههههه، عيوننا لك: "

    # لعبة الروليت النصية للإداريين
    if message.content.startswith('-روليت') or message.content.startswith('-roulette'):
        if not message.author.guild_permissions.manage_guild:
            await message.reply("❌ عذراً يا غالي، هذا الأمر مخصص للإداريين فقط!", delete_after=5)
            return

        view = RouletteView()
        embed = discord.Embed(
            title="🎰 سحب روليت Fynex",
            description="سوف تبدأ لعبه روليت اضغط الزر للمشاركه ⏳ (لديك 30 ثانية)",
            color=discord.Color.gold()
        )
        sent_msg = await message.channel.send(embed=embed, view=view)

        import asyncio
        await asyncio.sleep(30)

        if not view.participants:
            embed.description = "❌ انتهى الوقت ولم يشارك أحد في الروليت!"
            await sent_msg.edit(embed=embed, view=None)
            return

        winner = random.choice(view.participants)
        win_embed = discord.Embed(
            title="🎉 إعلان فائز الروليت",
            description=f"وقع الاختيار على ({winner.mention}) مبروك الفوز يا وحش! 🏆",
            color=discord.Color.green()
        )
        win_embed.set_thumbnail(url=winner.display_avatar.url)
        await sent_msg.edit(embed=win_embed, view=None)
        return

    if server_protections["anti_links"] and ("http://" in message.content or "https://" in message.content):
        if not message.author.guild_permissions.manage_messages:
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention} ممنوع إرسال الروابط هنا!", delete_after=5)
            except:
                pass
            return

    if server_protections["anti_spam"]:
        if not message.author.guild_permissions.manage_messages:
            current_time = time.time()
            timestamps = user_message_timestamps[uid]
            timestamps = [t for t in timestamps if current_time - t < TIME_WINDOW]
            timestamps.append(current_time)
            user_message_timestamps[uid] = timestamps
            
            if len(timestamps) > SPAM_LIMIT:
                try:
                    await message.delete()
                except:
                    pass
                user_warnings[uid] += 1
                if user_warnings[uid] < MAX_WARNINGS:
                    try:
                        warning_msg = await message.channel.send(f"⚠️ {message.author.mention}, توقف عن السبام!")
                        await warning_msg.delete(delay=5.0)
                    except:
                        pass
                else:
                    try:
                        await message.author.timeout(timedelta(minutes=5), reason="سبام")
                        await message.channel.send(f"🔇 تم كتم {message.author.mention} لمدة 5 دقائق.", delete_after=7)
                        user_warnings[uid] = 0
                    except:
                        pass
                return

    if message.channel.id == AI_CHANNEL_ID and not message.content.startswith('!'):
        reply_text = mood_prefix + random.choice(GENERAL_RESPONSES)
        await message.reply(reply_text)
        return

    await bot.process_commands(message)


# ==================== 4. نظام الفعاليات التلقائية ====================
@tasks.loop(minutes=45)
async def auto_event_task():
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                trivia_q = [
                    ("ما هي عاصمة المملكة العربية السعودية؟", "الرياض"),
                    ("كم عدد أركان الإسلام؟", "5"),
                    ("ما هو أسرع حيوان بري في العالم؟", "الفهد")
                ]
                q, a = random.choice(trivia_q)
                embed = discord.Embed(title="⚡ فعاليات Fynex التلقائية - سؤال سرعة!", description=f"**{q}**\n\nأول شخص يكتب الإجابة يفوز بجائزة مالية!", color=discord.Color.purple())
                try:
                    await channel.send(embed=embed)
                except:
                    pass
                break


# ==================== 🕹️ واجهات الأزرار (Views) ====================
class RouletteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.participants = []

    @discord.ui.button(label="انضمام للروليت 🎲", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participants:
            await interaction.response.send_message("❌ أنت مسجل مسبقاً!", ephemeral=True)
        else:
            self.participants.append(interaction.user)
            await interaction.response.send_message(f"✅ تم انضمامك بنجاح يا {interaction.user.mention}!", ephemeral=True)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


# لعبة من سيربح المليون
class MillionaireView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.question_step = 1

    @discord.ui.button(label="أ) الرياض", style=discord.ButtonStyle.blurple)
    async def choice_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ هذه اللعبة ليست لك!", ephemeral=True)
        
        if self.question_step == 1:
            embed = discord.Embed(title="🎮 من سيربح المليون - السؤال الثاني", description="ما هو أسرع حيوان بري؟\n\nأ) الأسد\nب) الفهد\nج) النمر\nد) الفيل", color=discord.Color.gold())
            self.question_step = 2
            button.label = "أ) الأسد"
            self.children[1].label = "ب) الفهد"
            self.children[2].label = "ج) النمر"
            self.children[3].label = "د) الفيل"
            await interaction.response.edit_message(embed=embed, view=self)
        elif self.question_step == 2:
            await interaction.response.edit_message(embed=discord.Embed(title="❌ إجابة خاطئة!", description="للأسف خسرت المسابقة!", color=discord.Color.red()), view=None)

    @discord.ui.button(label="ب) جده", style=discord.ButtonStyle.blurple)
    async def choice_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ هذه اللعبة ليست لك!", ephemeral=True)
        
        if self.question_step == 1:
            await interaction.response.edit_message(embed=discord.Embed(title="❌ إجابة خاطئة!", description="الإجابة الصحيحة كانت الرياض!", color=discord.Color.red()), view=None)
        elif self.question_step == 2:
            await interaction.response.edit_message(embed=discord.Embed(title="🏆 مبروك الفوز بالمليون!", description="لقد فزت بجائزة المليون عملة!", color=discord.Color.green()), view=None)
            user_balances[self.user_id] = user_balances.get(self.user_id, 100) + 1000000

    @discord.ui.button(label="ج) مكة", style=discord.ButtonStyle.blurple)
    async def choice_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ ليست لعبتك!", ephemeral=True)
        await interaction.response.edit_message(embed=discord.Embed(title="❌ إجابة خاطئة!", description="انتهت اللعبة.", color=discord.Color.red()), view=None)

    @discord.ui.button(label="د) الدمام", style=discord.ButtonStyle.blurple)
    async def choice_d(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ ليست لعبتك!", ephemeral=True)
        await interaction.response.edit_message(embed=discord.Embed(title="❌ إجابة خاطئة!", description="انتهت اللعبة.", color=discord.Color.red()), view=None)


# 10. لوحة التحكم للأزرار
class ControlPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="🛡️ تفعيل/تعطيل الروابط", style=discord.ButtonStyle.grey)
    async def toggle_links(self, interaction: discord.Interaction, button: discord.ui.Button):
        server_protections["anti_links"] = not server_protections["anti_links"]
        state = "مفعل ✅" if server_protections["anti_links"] else "مغلق ❌"
        await interaction.response.send_message(f"🔗 حماية الروابط أصبحت: **{state}**", ephemeral=True)

    @discord.ui.button(label="💬 تفعيل/تعطيل السبام", style=discord.ButtonStyle.grey)
    async def toggle_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        server_protections["anti_spam"] = not server_protections["anti_spam"]
        state = "مفعل ✅" if server_protections["anti_spam"] else "مغلق ❌"
        await interaction.response.send_message(f"💬 حماية السبام أصبحت: **{state}**", ephemeral=True)


# 3. الاقتراحات
class SuggestionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.yes = 0
        self.no = 0

    @discord.ui.button(label="موافق 👍", style=discord.ButtonStyle.green, custom_id="yes_sug")
    async def yes_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.yes += 1
        button.label = f"موافق 👍 ({self.yes})"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="غير موافق 👎", style=discord.ButtonStyle.red, custom_id="no_sug")
    async def no_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.no += 1
        button.label = f"غير موافق 👎 ({self.no})"
        await interaction.response.edit_message(view=self)


# تصويت عصابة أولد سكول
class OldSchoolVoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="👑 التصويت لأفضل إداري/عضو متفاعل", style=discord.ButtonStyle.blurple)
    async def vote_admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗳️ تم احتساب صوتك بنجاح ضمن فعاليات عصابة أولد سكول (Old School)!", ephemeral=True)


# ==================== 🛠️ الأوامر باللغة العربية (Slash Commands) ====================

@app_commands.command(name="تحديث_الأوامر", description="مزامنة وتحديث أوامر البوت في السيرفر")
@app_commands.default_permissions(manage_guild=True)
async def sync_cmd(interaction: discord.Interaction):
    try:
        synced = await bot.tree.sync()
        embed = discord.Embed(title="🔄 تمت المزامنة بنجاح!", description=f"تم تحديث **{len(synced)}** أمراً بالعربية.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ حدث خطأ: {e}", ephemeral=True)
bot.tree.add_command(sync_cmd)


@app_commands.command(name="لوحة_التحكم", description="10. لوحة تحكم البوت باستخدام الأزرار")
@app_commands.default_permissions(manage_guild=True)
async def control_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="🎛️ لوحة تحكم Fynex Bot السريعة", description="استخدم الأزرار للتحكم بحمايات السيرفر:", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=ControlPanelView(), ephemeral=True)
bot.tree.add_command(control_panel)


@app_commands.command(name="الحمايات", description="عرض حالة جميع الحمايات في السيرفر")
@app_commands.default_permissions(manage_guild=True)
async def protections(interaction: discord.Interaction):
    links_status = "مفعل ✅" if server_protections["anti_links"] else "غير مفعل ❌"
    spam_status = "مفعل ✅" if server_protections["anti_spam"] else "غير مفعل ❌"
    embed = discord.Embed(title="🛡️ لوحة حمايات Fynex Bot", color=discord.Color.dark_red())
    embed.add_field(name="🔗 حماية الروابط", value=links_status, inline=False)
    embed.add_field(name="💬 حماية السبام", value=spam_status, inline=False)
    await interaction.response.send_message(embed=embed)
bot.tree.add_command(protections)


@app_commands.command(name="مسح", description="مسح عدد معين من الرسائل")
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, عدد_الرسائل: int):
    if عدد_الرسائل < 1 or عدد_الرسائل > 100:
        return await interaction.response.send_message("❌ حدد بين 1 و 100.", ephemeral=True)
    await interaction.channel.purge(limit=عدد_الرسائل)
    await interaction.response.send_message(f"🛡️ تم مسح **{عدد_الرسائل}** رسالة بنجاح.", ephemeral=True)
bot.tree.add_command(clear)


@app_commands.command(name="قفل", description="قفل الروم الحالي")
@app_commands.default_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 تم قفل الروم بنجاح.")
bot.tree.add_command(lock)


@app_commands.command(name="فتح", description="فتح الروم الحالي")
@app_commands.default_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 تم فتح الروم بنجاح.")
bot.tree.add_command(unlock)


@app_commands.command(name="كتم_صوتي", description="كتم العضو في الروم الصوتي")
@app_commands.default_permissions(mute_members=True)
async def mute(interaction: discord.Interaction, العضو: discord.Member, السبب: str = "بدون سبب"):
    if not العضو.voice:
        return await interaction.response.send_message("❌ العضو ليس في روم صوتي!", ephemeral=True)
    await العضو.edit(mute=True, reason=السبب)
    await interaction.response.send_message(f"🔇 تم كتم {العضو.mention} صوتياً.", ephemeral=True)
bot.tree.add_command(mute)


@app_commands.command(name="فك_الكتم_الصوتي", description="إلغاء الكتم الصوتي عن العضو")
@app_commands.default_permissions(mute_members=True)
async def unmute(interaction: discord.Interaction, العضو: discord.Member):
    if not العضو.voice:
        return await interaction.response.send_message("❌ العضو ليس في روم صوتي!", ephemeral=True)
    await العضو.edit(mute=False)
    await interaction.response.send_message(f"🔊 تم إلغاء الكتم الصوتي عن {العضو.mention}.", ephemeral=True)
bot.tree.add_command(unmute)


@app_commands.command(name="تايم_آوت", description="إعطاء ميوت كتابي مؤقت للعضو")
@app_commands.default_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, العضو: discord.Member, الدقائق: int, السبب: str = "بدون سبب"):
    await العضو.timeout(timedelta(minutes=الدقائق), reason=السبب)
    await interaction.response.send_message(f"⏳ تم إعطاء تايم آوت لـ {العضو.mention} لمدة {الدقائق} دقيقة.", ephemeral=True)
bot.tree.add_command(timeout)


@app_commands.command(name="طرد", description="طرد عضو من السيرفر (إدارة عليا)")
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, العضو: discord.Member, السبب: str = "بدون سبب"):
    await العضو.kick(reason=السبب)
    await interaction.response.send_message(f"👢 تم طرد {العضو.mention} من السيرفر.", ephemeral=True)
bot.tree.add_command(kick)


@app_commands.command(name="حظر", description="حظر عضو من السيرفر نهائياً (إدارة عليا)")
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, العضو: discord.Member, السبب: str = "بدون سبب"):
    await العضو.ban(reason=السبب)
    await interaction.response.send_message(f"🔨 تم حظر {العضو.mention} من السيرفر.", ephemeral=True)
bot.tree.add_command(ban)


# 5. الترحيب واختيار الإطار
@app_commands.command(name="تحديد_روم_الترحيب", description="تحديد روم الترحيب للأعضاء الجدد")
@app_commands.default_permissions(manage_guild=True)
async def set_welcome_channel(interaction: discord.Interaction, الروم: discord.TextChannel):
    guild_id = interaction.guild.id
    if guild_id not in welcome_settings:
        welcome_settings[guild_id] = {}
    welcome_settings[guild_id]["channel_id"] = الروم.id
    if "message" not in welcome_settings[guild_id]:
        welcome_settings[guild_id]["message"] = "أهلاً بك يا {member} في سيرفر **{server}**!"
    if "design" not in welcome_settings[guild_id]:
        welcome_settings[guild_id]["design"] = 2
    await interaction.response.send_message(f"✅ تم تحديد روم الترحيب في: {الروم.mention}", ephemeral=True)
bot.tree.add_command(set_welcome_channel)


@app_commands.command(name="تحديد_إطار_الترحيب", description="اختر رقم تصميم الإطار (من 2 إلى 10)")
@app_commands.default_permissions(manage_guild=True)
@app_commands.choices(رقم_التصميم=[
    app_commands.Choice(name="تصميم 2 (ذهبي)", value=2),
    app_commands.Choice(name="تصميم 3 (بنفسجي)", value=3),
    app_commands.Choice(name="تصميم 4 (أحمر)", value=4),
    app_commands.Choice(name="تصميم 5 (سماوي)", value=5)
])
async def set_welcome_design(interaction: discord.Interaction, رقم_التصميم: int):
    guild_id = interaction.guild.id
    if guild_id not in welcome_settings:
        welcome_settings[guild_id] = {}
    welcome_settings[guild_id]["design"] = رقم_التصميم
    await interaction.response.send_message(f"🎨 تم اختيار تصميم إطار الترحيب رقم **{رقم_التصميم}** بنجاح!", ephemeral=True)
bot.tree.add_command(set_welcome_design)


@app_commands.command(name="تحديد_رسالة_الترحيب", description="تخصيص رسالة الترحيب بالعضو")
@app_commands.default_permissions(manage_guild=True)
async def set_welcome_message(interaction: discord.Interaction, الرسالة: str):
    guild_id = interaction.guild.id
    if guild_id not in welcome_settings:
        welcome_settings[guild_id] = {"channel_id": None}
    welcome_settings[guild_id]["message"] = الرسالة
    await interaction.response.send_message(f"✨ تم تحديث رسالة الترحيب بنجاح.", ephemeral=True)
bot.tree.add_command(set_welcome_message)


# 7. الرتب التلقائية
@app_commands.command(name="تحديد_الرتبة_التلقائية", description="تحديد الرتبة التلقائية للأعضاء الجدد")
@app_commands.default_permissions(manage_guild=True)
async def set_autorole(interaction: discord.Interaction, الرتبة: discord.Role):
    guild_id = interaction.guild.id
    if guild_id not in welcome_settings:
        welcome_settings[guild_id] = {}
    welcome_settings[guild_id]["autorole_id"] = الرتبة.id
    await interaction.response.send_message(f"✅ سيتم منح الأعضاء الجدد رتبة: {الرتبة.mention}", ephemeral=True)
bot.tree.add_command(set_autorole)


# 6. تسجيل دخول وخروج الإدارة
@app_commands.command(name="تسجيل_دخول_الإدارة", description="تسجيل دخول المشرف للدوام")
@app_commands.default_permissions(manage_guild=True)
async def admin_login(interaction: discord.Interaction):
    uid = interaction.user.id
    admin_logs[uid] = {"status": "متواجد", "time": time.time()}
    await interaction.response.send_message(f"🟢 تم تسجيل دخول المشرف {interaction.user.mention} لمباشرة المهام.", ephemeral=True)
bot.tree.add_command(admin_login)


@app_commands.command(name="تسجيل_خروج_الإدارة", description="تسجيل خروج المشرف من الدوام")
@app_commands.default_permissions(manage_guild=True)
async def admin_logout(interaction: discord.Interaction):
    uid = interaction.user.id
    if uid in admin_logs:
        del admin_logs[uid]
    await interaction.response.send_message(f"🔴 تم تسجيل خروج المشرف {interaction.user.mention} من الدوام.", ephemeral=True)
bot.tree.add_command(admin_logout)


# 1. مستويات XP
@app_commands.command(name="المستوى", description="عرض مستواك ونقاط الـ XP")
async def rank(interaction: discord.Interaction, العضو: discord.Member = None):
    target = العضو or interaction.user
    uid = target.id
    embed = discord.Embed(title=f"📊 رتبة ومستوى {target.name}", color=discord.Color.blurple())
    embed.add_field(name="⭐ المستوى", value=str(user_level[uid]), inline=True)
    embed.add_field(name="✨ نقاط الخبرة", value=str(user_xp[uid]), inline=True)
    embed.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=embed)
bot.tree.add_command(rank)


# 2. السمعة
@app_commands.command(name="سمعة", description="إعطاء نقطة سمعة لعضو متميز")
async def rep(interaction: discord.Interaction, العضو: discord.Member):
    if العضو.id == interaction.user.id:
        return await interaction.response.send_message("❌ لا يمكنك إعطاء سمعة لنفسك!", ephemeral=True)
    user_rep[العضو.id] += 1
    await interaction.response.send_message(f"⭐ تم إعطاء نقطة سمعة لـ {العضو.mention}! إجمالي سمعته: **{user_rep[العضو.id]}**")
bot.tree.add_command(rep)


# 13. المزاج
@app_commands.command(name="تحديد_المزاج", description="تغيير أسلوب ردود البوت معك")
@app_commands.choices(المزاج=[
    app_commands.Choice(name="عادي", value="عادي"),
    app_commands.Choice(name="رسمي", value="رسمي"),
    app_commands.Choice(name="حماسي", value="حماسي"),
    app_commands.Choice(name="ساخر", value="ساخر")
])
async def set_mood(interaction: discord.Interaction, المزاج: str):
    user_mood[interaction.user.id] = المزاج
    await interaction.response.send_message(f"✨ تم ضبط أسلوب ردودي معك إلى: **{المزاج}**", ephemeral=True)
bot.tree.add_command(set_mood)


@app_commands.command(name="الرصيد", description="عرض رصيدك المالي")
async def balance(interaction: discord.Interaction):
    bal = user_balances.get(interaction.user.id, 100)
    await interaction.response.send_message(f"💰 رصيدك المالي: **{bal}** عملة 🪙", ephemeral=True)
bot.tree.add_command(balance)


@app_commands.command(name="يومي", description="استلام المكافأة اليومية")
async def daily(interaction: discord.Interaction):
    uid = interaction.user.id
    user_balances[uid] = user_balances.get(uid, 100) + 500
    await interaction.response.send_message(f"🎁 تم إضافة **500** عملة إلى رصيدك بنجاح! 💸")
bot.tree.add_command(daily)


# 3. الاقتراحات
@app_commands.command(name="اقتراح", description="إرسال اقتراح جديد للتصويت")
async def suggest(interaction: discord.Interaction, الاقتراح: str):
    embed = discord.Embed(title="💡 اقتراح جديد", description=الاقتراح, color=discord.Color.purple())
    embed.set_footer(text=f"صاحب الاقتراح: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    view = SuggestionView()
    await interaction.response.send_message("✅ تم نشر اقتراحك بنجاح للتصويت!", ephemeral=True)
    await interaction.channel.send(embed=embed, view=view)
bot.tree.add_command(suggest)


# تصويت عصابة أولد سكول
@app_commands.command(name="تصويت_أولد_سكول", description="تصويت خاص لعصابة أولد سكول لأفضل إداري أو عضو")
async def oldschool_vote(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏴‍☠️ تصويت عصابة أولد سكول (Old School)",
        description="صوّت الآن لاختيار أفضل إداري أو عضو متفاعل داخل عصابة Old School الرسمية! 🏆",
        color=discord.Color.dark_red()
    )
    view = OldSchoolVoteView()
    await interaction.response.send_message(embed=embed, view=view)
bot.tree.add_command(oldschool_vote)


# لعبة من سيربح المليون
@app_commands.command(name="من_سيربح_المليون", description="لعبة من سيربح المليون التفاعلية بالأزرار")
async def millionaire(interaction: discord.Interaction):
    embed = discord.Embed(title="🎮 مرحباً بك في لعبة من سيربح المليون!", description="السؤال الأول: ما هي عاصمة المملكة العربية السعودية؟\n\nأ) الرياض\nب) جده\nج) مكة\nد) الدمام", color=discord.Color.gold())
    view = MillionaireView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)
bot.tree.add_command(millionaire)


# 9. الإحصائيات
@app_commands.command(name="إحصائيات_السيرفر", description="عرض إحصائيات السيرفر الشاملة")
async def stats(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"📈 إحصائيات سيرفر {guild.name}", color=discord.Color.dark_blue())
    embed.add_field(name="👥 إجمالي الأعضاء", value=str(guild.member_count), inline=True)
    embed.add_field(name="💬 رومات الشات والصوت", value=str(len(guild.channels)), inline=True)
    embed.add_field(name="🛡️ رتب السيرفر", value=str(len(guild.roles)), inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await interaction.response.send_message(embed=embed)
bot.tree.add_command(stats)


@app_commands.command(name="بنق", description="عرض سرعة استجابة البوت")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 سرعة استجابة Fynex Bot: **{latency}ms**", ephemeral=True)
bot.tree.add_command(ping)


@app_commands.command(name="المساعدة", description="عرض جميع أوامر Fynex Bot الشاملة باللغة العربية")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🌟 قائمة أوامر Fynex Bot العربية", description="إذا لم تظهر الأوامر، اكتب `/تحديث_الأوامر`:", color=discord.Color.dark_embed())
    embed.add_field(name="⚙️ الأدوات الأساسية", value="`/تحديث_الأوامر` - `/إحصائيات_السيرفر` - `/بنق` - `/المساعدة`", inline=False)
    embed.add_field(name="🛡️ الإدارة والحمايات", value="`/لوحة_التحكم` - `/الحمايات` - `/مسح` - `/قفل` - `/فتح` - `/تسجيل_دخول_الإدارة` - `/تسجيل_خروج_الإدارة`", inline=False)
    embed.add_field(name="🛠️ الإدارة الصوتية والكتابية", value="`/كتم_صوتي` - `/فك_الكتم_الصوتي` - `/تايم_آوت` - `/طرد` - `/حظر`", inline=False)
    embed.add_field(name="🌸 الترحيب والإطارات", value="`/تحديد_روم_الترحيب` - `/تحديد_إطار_الترحيب` - `/تحديد_رسالة_الترحيب` - `/تحديد_الرتبة_التلقائية`", inline=False)
    embed.add_field(name="📊 المستويات والاقتصاد", value="`/المستوى` - `/سمعة` - `/الرصيد` - `/يومي` - `/تحديد_المزاج`", inline=False)
    embed.add_field(name="💡 التفاعل والألعاب", value="`/اقتراح` - `/تصويت_أولد_سكول` - `/من_سيربح_المليون` - `-روليت`", inline=False)
    embed.set_footer(text="Fynex Bot Ultimate Arabic Edition")
    await interaction.response.send_message(embed=embed)
bot.tree.add_command(help_cmd)

bot.run(os.getenv('TOKEN'))
