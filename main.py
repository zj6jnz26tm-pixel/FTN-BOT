import discord
from discord import app_commands
from discord.ext import commands

class FynxaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("[Fynxa Bot] تم مزامنة جميع الأوامر بنجاح.")

bot = FynxaBot()

# قواعد بيانات مؤقتة لتخزين إعدادات السيرفرات والأعضاء
warnings_db = {}
auto_responses = {}
ticket_settings = {}
welcome_settings = {}
protection_settings = {"enabled": False}
autoroles = {}
applications = {}
shortcuts_db = {}

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user}")

# ==========================================
# 1. أوامر الإشراف (حظر، طرد، تايم آوت، فك تايم آوت)
# ==========================================

@bot.tree.command(name="ban", description="حظر عضو من السيرفر")
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"✅ تم حظر العضو {member.mention} بنجاح. السبب: {reason}", ephemeral=True)

@bot.tree.command(name="kick", description="طرد عضو من السيرفر")
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"✅ تم طرد العضو {member.mention} بنجاح. السبب: {reason}", ephemeral=True)

@bot.tree.command(name="timeout", description="إعطاء تايم آوت لعضو")
@app_commands.default_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "بدون سبب"):
    duration = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await interaction.response.send_message(f"⏱️ تم إعطاء تايم آوت لـ {member.mention} لمدة {minutes} دقيقة. السبب: {reason}", ephemeral=True)

@bot.tree.command(name="untimeout", description="فك التايم آوت عن العضو")
@app_commands.default_permissions(moderate_members=True)
async def untimeout(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"🔓 تم فك التايم آوت عن {member.mention}.", ephemeral=True)


# ==========================================
# 2. أوامر الكتم الصوتي والديفين (Mute, Unmute, Deafen, Undeafen)
# ==========================================

@bot.tree.command(name="mute", description="كتم العضو صوتياً")
@app_commands.default_permissions(mute_members=True)
async def voice_mute(interaction: discord.Interaction, member: discord.Member):
    if member.voice:
        await member.edit(mute=True)
        await interaction.response.send_message(f"🔇 تم كتم {member.mention} صوتياً.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ العضو ليس في روم صوتي.", ephemeral=True)

@bot.tree.command(name="unmute", description="فك الكتم الصوتي عن العضو")
@app_commands.default_permissions(mute_members=True)
async def voice_unmute(interaction: discord.Interaction, member: discord.Member):
    if member.voice:
        await member.edit(mute=False)
        await interaction.response.send_message(f"🔊 تم فك الكتم الصوتي عن {member.mention}.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ العضو ليس في روم صوتي.", ephemeral=True)

@bot.tree.command(name="deafen", description="إعطاء ديفين (إسكات تام) للعضو")
@app_commands.default_permissions(deafen_members=True)
async def deafen(interaction: discord.Interaction, member: discord.Member):
    if member.voice:
        await member.edit(deafen=True)
        await interaction.response.send_message(f"🔇 تم عمل ديفين لـ {member.mention}.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ العضو ليس في روم صوتي.", ephemeral=True)

@bot.tree.command(name="undeafen", description="فك الديفين عن العضو")
@app_commands.default_permissions(deafen_members=True)
async def undeafen(interaction: discord.Interaction, member: discord.Member):
    if member.voice:
        await member.edit(deafen=False)
        await interaction.response.send_message(f"🔊 تم فك الديفين عن {member.mention}.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ العضو ليس في روم صوتي.", ephemeral=True)


# ==========================================
# 3. تغيير اسم العضو (Nickname)
# ==========================================

@bot.tree.command(name="nickname", description="تغيير لقب العضو في السيرفر")
@app_commands.default_permissions(manage_nicknames=True)
async def change_nickname(interaction: discord.Interaction, member: discord.Member, new_name: str):
    await member.edit(nick=new_name)
    await interaction.response.send_message(f"✏️ تم تغيير لقب العضو إلى: **{new_name}**", ephemeral=True)


# ==========================================
# 4. نظام الإنذارات (تحذير وعرض الإنذارات)
# ==========================================

@bot.tree.command(name="warn", description="تحذير عضو في السيرفر")
@app_commands.default_permissions(manage_messages=True)
async def warn_member(interaction: discord.Interaction, member: discord.Member, reason: str):
    guild_id = interaction.guild.id
    if guild_id not in warnings_db:
        warnings_db[guild_id] = {}
    if member.id not in warnings_db[guild_id]:
        warnings_db[guild_id][member.id] = []
    
    warnings_db[guild_id][member.id].append(reason)
    await interaction.response.send_message(f"⚠️ تم تحذير {member.mention} بنجاح. السبب: {reason}", ephemeral=True)

@bot.tree.command(name="warnings", description="عرض قائمة إنذارات الأعضاء في السيرفر")
@app_commands.default_permissions(manage_messages=True)
async def show_warnings(interaction: discord.Interaction, member: discord.Member):
    guild_id = interaction.guild.id
    user_warns = warnings_db.get(guild_id, {}).get(member.id, [])
    
    if not user_warns:
        await interaction.response.send_message(f"✅ العضو {member.mention} ليس لديه أي إنذارات.", ephemeral=True)
    else:
        warns_list = "\n".join([f"- {w}" for w in user_warns])
        await interaction.response.send_message(f"📋 قائمة إنذارات {member.mention}:\n{warns_list}", ephemeral=True)


# ==========================================
# 5. الرد التلقائي (تحديد الكلمة والرد)
# ==========================================

@bot.tree.command(name="autoresponder", description="إعداد الرد التلقائي وتحديد نص الرد والرد الذي يرسله البوت")
@app_commands.default_permissions(manage_guild=True)
async def autoresponder(interaction: discord.Interaction, trigger: str, reply: str):
    guild_id = interaction.guild.id
    if guild_id not in auto_responses:
        auto_responses[guild_id] = {}
    
    auto_responses[guild_id][trigger] = reply
    await interaction.response.send_message(f"🤖 تمت إضافة الرد التلقائي بنجاح:\n- الكلمة المفتاحية: `{trigger}`\n- الرد: `{reply}`", ephemeral=True)


# ==========================================
# 6. نموذج التقديم وتخصيصه
# ==========================================

@bot.tree.command(name="set_application", description="نموذج التقديم وتخصيص الأسئلة")
@app_commands.default_permissions(administrator=True)
async def set_application(interaction: discord.Interaction, questions: str):
    guild_id = interaction.guild.id
    applications[guild_id] = questions
    await interaction.response.send_message(f"📝 تم تحديث وتخصيص نموذج التقديم بنجاح.", ephemeral=True)


# ==========================================
# 7. تحديد الرولات التلقائية للأعضاء الجدد
# ==========================================

@bot.tree.command(name="set_autorole", description="تحديد الرولات التلقائية التي تُعطى للأعضاء الجدد")
@app_commands.default_permissions(administrator=True)
async def set_autorole(interaction: discord.Interaction, role: discord.Role):
    guild_id = interaction.guild.id
    autoroles[guild_id] = role.id
    await interaction.response.send_message(f"👑 تم تعيين الرول التلقائي بنجاح: {role.mention}", ephemeral=True)


# ==========================================
# 8. حمايات السيرفر (تفعيل / تعطيل + كشف)
# ==========================================

@bot.tree.command(name="protection", description="نظام حمايات السيرفر تفعيل / تعطيل")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(status=[
    app_commands.Choice(name="تفعيل", value="on"),
    app_commands.Choice(name="تعطيل", value="off")
])
async def protection(interaction: discord.Interaction, status: str):
    protection_settings["enabled"] = (status == "on")
    await interaction.response.send_message(f"🛡️ تم تغيير حالة حماية السيرفر إلى: **{status}**", ephemeral=True)

@bot.tree.command(name="protection_status", description="كشف حالة حماية السيرفر الحالية")
@app_commands.default_permissions(administrator=True)
async def protection_status(interaction: discord.Interaction):
    status = "مفعل ✅" if protection_settings.get("enabled", False) else "معطل ❌"
    await interaction.response.send_message(f"🔍 حالة حماية السيرفر الحالية: {status}", ephemeral=True)


# ==========================================
# 9. نظام التكت (تفعيل/تعطيل + ذكر السبب + روم السجلات)
# ==========================================

@bot.tree.command(name="tickets", description="نظام التكت / تفعيل تعطيل، ذكر السبب قبل الفتح، وتحديد روم السجلات")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(status=[
    app_commands.Choice(name="تفعيل", value="enable"),
    app_commands.Choice(name="تعطيل", value="disable")
])
async def tickets(interaction: discord.Interaction, status: str, log_channel: discord.TextChannel, require_reason: bool):
    guild_id = interaction.guild.id
    ticket_settings[guild_id] = {
        "status": status,
        "channel": log_channel.id,
        "require_reason": require_reason
    }
    await interaction.response.send_message(f"🎫 تم حفظ إعدادات التذاكر:\n- الحالة: **{status}**\n- روم التذاكر المنتهية: {log_channel.mention}\n- طلب السبب قبل الفتح: **{require_reason}**", ephemeral=True)


# ==========================================
# 10. إدارة اختصارات البوت
# ==========================================

@bot.tree.command(name="shortcuts", description="إدارة اختصارات الأوامر الخاصة بالبوت")
@app_commands.default_permissions(manage_guild=True)
async def shortcuts(interaction: discord.Interaction, name: str, command_mapping: str):
    guild_id = interaction.guild.id
    if guild_id not in shortcuts_db:
        shortcuts_db[guild_id] = {}
    
    shortcuts_db[guild_id][name] = command_mapping
    await interaction.response.send_message(f"⚡ تم إضافة الاختصار `{name}` بنجاح ليرتبط بـ: `{command_mapping}`", ephemeral=True)


# ==========================================
# 11. نظام الترحيب (تفعيل/تعطيل، الصورة، النص، والتصميم)
# ==========================================

@bot.tree.command(name="welcome", description="إعداد نظام الترحيب (تفعيل/تعطيل، روم، نص، وعرض الصورة)")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(status=[
    app_commands.Choice(name="تفعيل", value="on"),
    app_commands.Choice(name="تعطيل", value="off")
])
async def welcome(interaction: discord.Interaction, status: str, channel: discord.TextChannel, message: str, show_avatar: bool):
    guild_id = interaction.guild.id
    if guild_id not in welcome_settings:
        welcome_settings[guild_id] = {}
        
    welcome_settings[guild_id].update({
        "status": status,
        "channel": channel.id,
        "message": message,
        "show_avatar": show_avatar
    })
    await interaction.response.send_message(f"✨ تم حفظ إعدادات الترحيب بنجاح في الروم {channel.mention}.", ephemeral=True)

@bot.tree.command(name="set_welcome_design", description="تحديد رقم تصميم بطاقة الترحيب")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(رقم_التصميم=[
    app_commands.Choice(name="تصميم 1", value=1),
    app_commands.Choice(name="تصميم 2", value=2),
    app_commands.Choice(name="تصميم 3", value=3),
    app_commands.Choice(name="تصميم 4", value=4),
    app_commands.Choice(name="تصميم 5", value=5),
    app_commands.Choice(name="تصميم 6", value=6),
    app_commands.Choice(name="تصميم 7", value=7),
    app_commands.Choice(name="تصميم 8", value=8),
    app_commands.Choice(name="تصميم 9", value=9),
    app_commands.Choice(name="تصميم 10", value=10),
])
async def set_welcome_design(interaction: discord.Interaction, رقم_التصميم: int):
    guild_id = interaction.guild.id
    if guild_id not in welcome_settings:
        welcome_settings[guild_id] = {}
        
    welcome_settings[guild_id]["design"] = رقم_التصميم
    await interaction.response.send_message(f"🎨 تم تحديد تصميم الترحيب رقم: **{رقم_التصميم}** بنجاح.", ephemeral=True)


# تشغيل البوت بالتوكن الخاص بك
bot.run("YOUR_BOT_TOKEN")
