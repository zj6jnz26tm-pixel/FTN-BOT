
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
GAMES_CHANNEL_ID = None  # يمكن تعيينه لاحقاً عبر أمر أو تركها عامة

# ==================== قواعد البيانات المؤقتة ====================
user_balances = {}
user_xp = defaultdict(int)
user_level = defaultdict(int)
user_rep = defaultdict(int)
user_mood = defaultdict(lambda: "عادي") # مزاج البوت مع العضو

server_protections = {
    "anti_links": True,
    "anti_spam": True,
    "anti_bots": False
}

welcome_settings = {} # {guild_id: {"channel_id": id, "message": "...", "autorole_id": id}}
suggestion_settings = {} # {guild_id: channel_id}
admin_logs = {} # {user_id: {"status": "مفعل", "time": ...}}

user_message_timestamps = defaultdict(list)
user_warnings = defaultdict(int)

SPAM_LIMIT = 4
TIME_WINDOW = 5.0
MAX_WARNINGS = 3


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} | Fynex Bot Online 🚀')
    auto_event_task.start()


# ==================== 🌸 نظام الترحيب والرتب التلقائية ====================
@bot.event
async def on_member_join(member: discord.Member):
    guild_id = member.guild.id
    
    # 7. نظام إعطاء رتب تلقائية (Auto-Role)
    if guild_id in welcome_settings and "autorole_id" in welcome_settings[guild_id]:
        role_id = welcome_settings[guild_id]["autorole_id"]
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
            except:
                pass

    # 5. نظام ترحيب بصورة العضو وإطار دائري
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
        avatar_img = avatar_img.resize((150, 150))

        mask = Image.new("L", (150, 150), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 150, 150), fill=255)

        output_img = Image.new("RGBA", (170, 170), (0, 0, 0, 0))
        draw_frame = ImageDraw.Draw(output_img)
        draw_frame.ellipse((0, 0, 170, 170), fill=(255, 215, 0, 255))
        output_img.paste(avatar_img, (10, 10), mask=mask)

        buffer = io.BytesIO()
        output_img.save(buffer, format="PNG")
        buffer.seek(0)

        file = discord.File(buffer, filename="welcome_avatar.png")

        embed = discord.Embed(
            title="✨ عضو جديد انضم إلينا!",
            description=formatted_msg,
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="attachment://welcome_avatar.png")
        embed.add_field(name="📊 ترتيبك بين الأعضاء", value=f"رقم العضو: #{member.guild.member_count}", inline=False)
        embed.set_footer(text=f"نورت سيرفر {member.guild.name}", icon_url=member.guild.icon.url if member.guild.icon else None)

        await channel.send(embed=embed, file=file)
    except Exception as e:
        print(f"Error in welcome event: {e}")


# ==================== 💬 نظام الرسائل والمستويات والمزاج ====================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. نظام مستويات XP
    uid = message.author.id
    user_xp[uid] += random.randint(5, 15)
    current_xp = user_xp[uid]
    next_level_xp = (user_level[uid] + 1) * 100
    if current_xp >= next_level_xp:
        user_level[uid] += 1
        await message.channel.send(f"🎉 مبروك يا {message.author.mention}! لقد صعدت إلى المستوى **{user_level[uid]}** 🚀!")

    # 13. نظام مزاج البوت: تغيير أسلوب الردود حسب شخصية العضو
    mood = user_mood[uid]
    mood_prefix = ""
    if mood == "رسمي":
        mood_prefix = "نظراً لطلبك، تفضل: "
    elif mood == "حماسي":
        mood_prefix = "يا وحش! 🔥 "
    elif mood == "ساخر":
        mood_prefix = "ههههه، عيوننا لك: "

    # الأوامر النصية العادية (مثل -روليت)
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
        embed.set_footer(text="Fynex Bot Events")
        
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
        win_embed.set_footer(text="Fynex Bot Roulette Winner")

        await sent_msg.edit(embed=win_embed, view=None)
        return

    # حماية الروابط
    if server_protections["anti_links"] and ("http://" in message.content or "https://" in message.content):
        if not message.author.guild_permissions.manage_messages:
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention} ممنوع إرسال الروابط هنا!", delete_after=5)
            except:
                pass
            return

    # حماية السبام
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
                current_warnings = user_warnings[uid]
                
                if current_warnings < MAX_WARNINGS:
                    try:
                        warning_msg = await message.channel.send(f"⚠️ {message.author.mention}, يرجى التوقف عن السبام! ({current_warnings}/{MAX_WARNINGS})")
                        await warning_msg.delete(delay=5.0)
                    except:
                        pass
                else:
                    try:
                        await message.author.timeout(timedelta(minutes=5), reason="سبام")
                        await message.channel.send(f"🔇 تم كتم {message.author.mention} لمدة 5 دقائق بسبب السبام.", delete_after=7)
                        user_warnings[uid] = 0
                    except:
                        pass
                return

    # الرد الآلي في روم الـ AI
    if message.channel.id == AI_CHANNEL_ID and not message.content.startswith('!'):
        GENERAL_RESPONSES = [
            "يا هلا! أنا معك، اسأل اللي بخاطرك وأنا أخوك في روم الـ AI ✨",
            "صدقت! عاد علمنا، وش وديان السوالف اليوم في سيرفرنا؟",
            "ممم.. نقطة مهمة! شاركنا تفاصيل أكثر عشان نفيدك أكثر يا غالي.",
            "أنا حاضر وموجود طوال الوقت، تفضل اطرح سؤالك أو موضوعك!"
        ]
        reply_text = mood_prefix + random.choice(GENERAL_RESPONSES)
        await message.reply(reply_text)
        return

    await bot.process_commands(message)


# ==================== 🎮 نظام الفعاليات التلقائية ====================
@tasks.loop(minutes=45)
async def auto_event_task():
    # يبحث عن أول روم نصي لإرسال الفعالية التلقائية (سؤال سرعة)
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                trivia_q = [
                    ("ما هو عاصمة المملكة العربية السعودية؟", "الرياض"),
                    ("كم عدد أركان الإسلام؟", "5"),
                    ("ما هو أسرع حيوان بري في العالم؟", "الفهد")
                ]
                q, a = random.choice(trivia_q)
                embed = discord.Embed(title="⚡ فعاليات Fynex التلقائية - سؤال سرعة!", description=f"**{q}**\n\nأول شخص يكتب الإجابة الصحيحة بالشات يفوز بنقاط وسفرة مالية!", color=discord.Color.purple())
                await channel.send(embed=embed)
                break


# ==================== 🕹️ أزرار الألعاب والفعاليات ====================
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


# ==================== 💰 لعبة من سيربح المليون ====================
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
            embed = discord.Embed(title="🎮 من سيربح المليون - السؤال الثاني", description="ما هو أسرع حيوان بري؟\n\nأ) الأسد\nب) الفهد (Correct)\nج) النمر\nد) الفيل", color=discord.Color.gold())
            self.question_step = 2
            # تعديل الأزرار للسؤال الثاني
            button.label = "أ) الأسد"
            self.children[1].label = "ب) الفهد"
            self.children[2].label = "ج) النمر"
            self.children[3].label = "د) الفيل"
            await interaction.response.edit_message(embed=embed, view=self)
        elif self.question_step == 2:
            # إجابة خاطئة للسؤال الثاني لو اختار أ
            await interaction.response.edit_message(embed=discord.Embed(title="❌ إجابة خاطئة!", description="للأسف خَسِرت المسابقة، حاول مرة أخرى!", color=discord.Color.red()), view=None)

    @discord.ui.button(label="ب) جده", style=discord.ButtonStyle.blurple)
    async def choice_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ هذه اللعبة ليست لك!", ephemeral=True)
        
        if self.question_step == 1:
            await interaction.response.edit_message(embed=discord.Embed(title="❌ إجابة خاطئة!", description="الإجابة الصحيحة كانت الرياض!", color=discord.Color.red()), view=None)
        elif self.question_step == 2:
            # إجابة صحيحة للسؤال الثاني (الفهد)
            await interaction.response.edit_message(embed=discord.Embed(title="🏆 مبروك الفوز بالمليون!", description="لقد أزلت كل الأسئلة بنجاح وفزت بجائزة المليون عملة في Fynex!", color=discord.Color.green()), view=None)
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


# ==================== 🛠️ لوحة التحكم بالأزرار (Dashboard) ====================
class ControlPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="🛡️ تفعيل/تعطيل الروابط", style=discord.ButtonStyle.grey)
    async def toggle_links(self, interaction: discord.Interaction, button: discord.ui.Button):
        server_protections["anti_links"] = not server_protections["anti_links"]
        state = "مفعل ✅" if server_protections["anti_links"] else "مغلق ❌"
        await interaction.response.send_message(f"🔗 أصبحت حماية الروابط الآن: **{state}**", ephemeral=True)

    @discord.ui.button(label="💬 تفعيل/تعطيل السبام", style=discord.ButtonStyle.grey)
    async def toggle_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        server_protections["anti_spam"] = not server_protections["anti_spam"]
        state = "مفعل ✅" if server_protections["anti_spam"] else "مغلق ❌"
        await interaction.response.send_message(f"💬 أصبحت حماية السبام الآن: **{state}**", ephemeral=True)


# ==================== ⚙️ الأوامر والأنظمة الجديدة ====================

@bot.tree.command(name="control_panel", description="10. لوحة تحكم البوت باستخدام الأزرار")
@app_commands.default_permissions(manage_guild=True)
async def control_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="🎛️ لوحة تحكم Fynex Bot السريعة", description="استخدم الأزرار أدناه للتحكم بإعدادات السيرفر الفورية:", color=discord.Color.blue())
    view = ControlPanelView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="rank", description="1. عرض مستواك ونقاط الـ XP الحالية")
async def rank(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    uid = target.id
    embed = discord.Embed(title=f"📊 رتبة ومستوى {target.name}", color=discord.Color.blurple())
    embed.add_field(name="⭐ المستوى", value=str(user_level[uid]), inline=True)
    embed.add_field(name="✨ نقاط الخبرة (XP)", value=str(user_xp[uid]), inline=True)
    embed.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="rep", description="2. إعطاء نقطة سمعة لعضو متميز")
async def rep(interaction: discord.Interaction, member: discord.Member):
    if member.id == interaction.user.id:
        return await interaction.response.send_message("❌ لا يمكنك إعطاء سمعة لنفسك!", ephemeral=True)
    user_rep[member.id] += 1
    embed = discord.Embed(title="⭐ نقاط السمعة", description=f"تم إعطاء نقطة سمعة بنجاح إلى {member.mention}! إجمالي سمعته: **{user_rep[member.id]}**", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed)


# 3. نظام اقتراحات مع تصويت
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

@bot.tree.command(name="suggest", description="3. إرسال اقتراح جديد للتصويت عليه")
async def suggest(interaction: discord.Interaction, اقتراحك: str):
    embed = discord.Embed(title="💡 اقتراح جديد", description=اقتراحك, color=discord.Color.purple())
    embed.set_footer(text=f"صاحب الاقتراح: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    view = SuggestionView()
    await interaction.response.send_message("✅ تم نشر اقتراحك بنجاح للتصويت!", ephemeral=True)
    await interaction.channel.send(embed=embed, view=view)


# 6. نظام تسجيل دخول وخروج الإدارة
@bot.tree.command(name="admin_login", description="6. تسجيل دخول الإدارة للدوام")
@app_commands.default_permissions(manage_guild=True)
async def admin_login(interaction: discord.Interaction):
    uid = interaction.user.id
    admin_logs[uid] = {"status": "متواجد", "time": time.time()}
    embed = discord.Embed(title="🟢 تسجيل دخول إداري", description=f"تم تسجيل دخول المشرف {interaction.user.mention} لمباشرة المهام.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="admin_logout", description="6. تسجيل خروج الإدارة من الدوام")
@app_commands.default_permissions(manage_guild=True)
async def admin_logout(interaction: discord.Interaction):
    uid = interaction.user.id
    if uid in admin_logs:
        del admin_logs[uid]
    embed = discord.Embed(title="🔴 تسجيل خروج إداري", description=f"تم تسجيل خروج المشرف {interaction.user.mention} من الدوام.", color=discord.Color.red())
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="set_autorole", description="7. تحديد الرتبة التلقائية للأعضاء الجدد")
@app_commands.default_permissions(manage_guild=True)
async def set_autorole(interaction: discord.Interaction, role: discord.Role):
    guild_id = interaction.guild.id
    if guild_id not in welcome_settings:
        welcome_settings[guild_id] = {}
    welcome_settings[guild_id]["autorole_id"] = role.id
    embed = discord.Embed(title="✅ تم ضبط الرتبة التلقائية", description=f"سيتم منح الأعضاء الجدد رتبة: {role.mention}", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)


# 8. نظام ألعاب داخل روم محدد
@bot.tree.command(name="millionaire", description="لعبة من سيربح المليون الاحترافية")
async def millionaire(interaction: discord.Interaction):
    embed = discord.Embed(title="🎮 مرحباً بك في لعبة من سيربح المليون!", description="السؤال الأول: ما هي عاصمة المملكة العربية السعودية؟\n\nأ) الرياض\nب) جده\nج) مكة\nد) الدمام", color=discord.Color.gold())
    view = MillionaireView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)


# 9. نظام إحصائيات السيرفر
@bot.tree.command(name="stats", description="9. عرض إحصائيات السيرفر الشاملة")
async def stats(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"📈 إحصائيات سيرفر {guild.name}", color=discord.Color.dark_blue())
    embed.add_field(name="👥 إجمالي الأعضاء", value=str(guild.member_count), inline=True)
    embed.add_field(name="💬 رومات الشات والصوت", value=str(len(guild.channels)), inline=True)
    embed.add_field(name="🛡️ رتب السيرفر", value=str(len(guild.roles)), inline=True)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await interaction.response.send_message(embed=embed)


# أمر تصويت خاص لعصابة أولد سكول (Old School)
class OldSchoolVoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.votes = defaultdict(int)

    @discord.ui.button(label="👑 التصويت لأفضل إداري", style=discord.ButtonStyle.blurple)
    async def vote_admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🗳️ تم احتساب صوتك ضمن فعاليات عصابة أولد سكول للأفضل!", ephemeral=True)

@bot.tree.command(name="oldschool_vote", description="تصويت خاص لعصابة أولد سكول لأفضل إداري أو عضو")
async def oldschool_vote(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏴‍☠️ تصويت عصابة أولد سكول (Old School)",
        description="صوّت الآن لاختيار أفضل إداري أو عضو متفاعل داخل عصابة Old School الرسمية! 🏆",
        color=discord.Color.dark_red()
    )
    view = OldSchoolVoteView()
    await interaction.response.send_message(embed=embed, view=view)


# 13. نظام تغيير المزاج
@bot.tree.command(name="set_mood", description="13. تغيير أسلوب ردود البوت معك (رسمي، حماسي، ساخر، عادي)")
@app_commands.choices(mood=[
    app_commands.Choice(name="عادي", value="عادي"),
    app_commands.Choice(name="رسمي", value="رسمي"),
    app_commands.Choice(name="حماسي", value="حماسي"),
    app_commands.Choice(name="ساخر", value="ساخر")
])
async def set_mood(interaction: discord.Interaction, mood: str):
    user_mood[interaction.user.id] = mood
    embed = discord.Embed(title="✨ تحديث المزاج", description=لأصدقائي، تم ضبط أسلوب ردودي معك إلى: **{mood}**", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)


# تحديث أمر Help ليشمل الأوامر الجديدة
@bot.tree.command(name="help", description="عرض جميع أوامر Fynex Bot المحدثة")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🌟 قائمة أوامر Fynex Bot الشاملة", description="جميع الأنظمة والخصائص المضافة بنجاح:", color=discord.Color.dark_embed())
    embed.add_field(name="📊 المستويات والسمعة", value="`/rank` - `/rep`", inline=False)
    embed.add_field(name="💡 التفاعل والاقتراحات", value="`/suggest` - `/oldschool_vote` - `/set_mood`", inline=False)
    embed.add_field(name="🎮 الألعاب والفعاليات", value="`/millionaire` - `-روليت`", inline=False)
    embed.add_field(name="🛡️ الإدارة والحمايات", value="`/control_panel` - `/admin_login` - `/admin_logout` - `/set_autorole`", inline=False)
    embed.add_field(name="🌸 الترحيب والإحصائيات", value="`/set_welcome_channel` - `/set_welcome_message` - `/stats`", inline=False)
    embed.set_footer(text="Fynex Bot Ultimate Elite Version")
    await interaction.response.send_message(embed=embed)


bot.run(os.getenv('TOKEN'))
