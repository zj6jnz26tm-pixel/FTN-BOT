
import os
import random
import time
from datetime import timedelta
from collections import defaultdict
import discord
from discord import app_commands
from discord.ext import commands

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

GENERAL_RESPONSES = [
    "يا هلا! أنا معك، اسأل اللي بخاطرك وأنا أخوك في روم الـ AI ✨",
    "صدقت! عاد علمنا، وش وديان السوالف اليوم في سيرفرنا؟",
    "ممم.. نقطة مهمة! شاركنا تفاصيل أكثر عشان نفيدك أكثر يا غالي.",
    "أنا حاضر وموجود طوال الوقت، تفضل اطرح سؤالك أو موضوعك!",
    "الله يقويك! كيف أقدر أساعدك بهذا الخصوص؟",
    "يا سلام عليك! اسأل اللي تبيه، كلنا كذا جاهزين لخدمتك."
]

user_balances = {}

server_protections = {
    "anti_links": True,
    "anti_spam": True,
    "anti_bots": False
}

user_message_timestamps = defaultdict(list)
user_warnings = defaultdict(int)

SPAM_LIMIT = 4
TIME_WINDOW = 5.0
MAX_WARNINGS = 3


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} | Fynex Bot Online 🚀')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

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
            user_id = message.author.id
            current_time = time.time()
            
            timestamps = user_message_timestamps[user_id]
            timestamps = [t for t in timestamps if current_time - t < TIME_WINDOW]
            timestamps.append(current_time)
            user_message_timestamps[user_id] = timestamps
            
            if len(timestamps) > SPAM_LIMIT:
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
                
                user_warnings[user_id] += 1
                current_warnings = user_warnings[user_id]
                
                if current_warnings < MAX_WARNINGS:
                    try:
                        warning_msg = await message.channel.send(
                            f"⚠️ {message.author.mention}, يرجى التوقف عن السبام! (تحذير {current_warnings}/{MAX_WARNINGS})"
                        )
                        await warning_msg.delete(delay=5.0)
                    except:
                        pass
                else:
                    try:
                        await message.author.timeout(timedelta(minutes=5), reason="تجاوز حد التحذيرات للسبام")
                        punish_msg = await message.channel.send(
                            f"🔇 تم كتم العضو {message.author.mention} لمدة 5 دقائق بسبب استمرار السبام."
                        )
                        await punish_msg.delete(delay=7.0)
                        user_warnings[user_id] = 0
                    except discord.Forbidden:
                        pass
                return

    if message.channel.id == AI_CHANNEL_ID and not message.content.startswith('!'):
        reply_text = random.choice(GENERAL_RESPONSES)
        await message.reply(reply_text)
        return

    await bot.process_commands(message)

# ==================== 🎮 أزرار الروليت ====================

class RouletteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.participants = []

    @discord.ui.button(label="انضمام للروليت 🎲", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.participants:
            await interaction.response.send_message("❌ أنت مسجل مسبقاً في هذه اللعبة!", ephemeral=True)
        else:
            self.participants.append(interaction.user)
            await interaction.response.send_message(f"✅ تم انضمامك بنجاح يا {interaction.user.mention}!", ephemeral=True)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


# ==================== 🛡️ نظام الحمايات والإدارة ====================

@bot.tree.command(name="protections", description="عرض حالة جميع الحمايات في السيرفر")
@app_commands.default_permissions(manage_guild=True)
async def protections(interaction: discord.Interaction):
    links_status = "مفعل ✅" if server_protections["anti_links"] else "غير مفعل ❌"
    spam_status = "مفعل ✅" if server_protections["anti_spam"] else "غير مفعل ❌"
    bots_status = "مفعل ✅" if server_protections["anti_bots"] else "غير مفعل ❌"

    embed = discord.Embed(title="🛡️ لوحة حمايات Fynex Bot", description="حالة الحمايات الحالية في السيرفر:", color=discord.Color.dark_red())
    embed.add_field(name="🔗 حماية الروابط (anti_links)", value=links_status, inline=False)
    embed.add_field(name="💬 حماية السبام (anti_spam)", value=spam_status, inline=False)
    embed.add_field(name="🤖 حماية البوتات (anti_bots)", value=bots_status, inline=False)
    embed.set_footer(text="لتغيير الحالة استخدم أمر /toggle_protection")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="toggle_protection", description="تفعيل أو تعطيل حماية معينة")
@app_commands.default_permissions(manage_guild=True)
@app_commands.choices(protection=[
    app_commands.Choice(name="حماية الروابط (anti_links)", value="anti_links"),
    app_commands.Choice(name="حماية السبام (anti_spam)", value="anti_spam"),
    app_commands.Choice(name="حماية البوتات (anti_bots)", value="anti_bots")
], status=[
    app_commands.Choice(name="تفعيل (On)", value="on"),
    app_commands.Choice(name="تعطيل (Off)", value="off")
])
async def toggle_protection(interaction: discord.Interaction, protection: str, status: str):
    is_on = True if status == "on" else False
    server_protections[protection] = is_on
    
    state_text = "تفعيلها ✅" if is_on else "تعطيلها ❌"
    embed = discord.Embed(title="🛡️ تحديث نظام الحماية", description=f"تم **{state_text}** بنجاح للحماية المطلوبة.", color=discord.Color.green() if is_on else discord.Color.red())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear", description="مسح عدد معين من الرسائل")
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ حدد بين 1 و 100.", ephemeral=True)
        return
    await interaction.channel.purge(limit=amount)
    embed = discord.Embed(title="🛡️ مسح الرسائل", description=f"تم مسح **{amount}** رسالة بنجاح.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="lock", description="قفل الروم الحالي")
@app_commands.default_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    embed = discord.Embed(title="🔒 قفل الروم", description="تم قفل الروم بنجاح.", color=discord.Color.dark_red())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="unlock", description="فتح الروم الحالي")
@app_commands.default_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    embed = discord.Embed(title="🔓 فتح الروم", description="تم فتح الروم بنجاح.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)


# ==================== 🛠️ الأوامر الإدارية الجديدة ====================

@bot.tree.command(name="mute", description="كتم العضو في الروم الصوتي")
@app_commands.default_permissions(mute_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
    if not member.voice:
        await interaction.response.send_message("❌ العضو ليس في روم صوتي حالياً!", ephemeral=True)
        return
    await member.edit(mute=True, reason=reason)
    await interaction.response.send_message(f"🔇 تم كتم العضو {member.mention} صوتياً بنجاح.", ephemeral=True)

@bot.tree.command(name="unmute", description="إلغاء الكتم الصوتي عن العضو")
@app_commands.default_permissions(mute_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if not member.voice:
        await interaction.response.send_message("❌ العضو ليس في روم صوتي حالياً!", ephemeral=True)
        return
    await member.edit(mute=False)
    await interaction.response.send_message(f"🔊 تم إلغاء الكتم الصوتي عن العضو {member.mention}.", ephemeral=True)

@bot.tree.command(name="move", description="نقل عضو إلى روم صوتي آخر")
@app_commands.default_permissions(move_members=True)
async def move(interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel):
    if not member.voice:
        await interaction.response.send_message("❌ العضو ليس متصلاً بأي روم صوتي!", ephemeral=True)
        return
    await member.move_to(channel)
    await interaction.response.send_message(f"🔀 تم نقل العضو {member.mention} إلى الروم {channel.mention}.", ephemeral=True)

@bot.tree.command(name="deafen", description="إصمام (Deafen) العضو في الروم الصوتي")
@app_commands.default_permissions(deafen_members=True)
async def deafen(interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
    if not member.voice:
        await interaction.response.send_message("❌ العضو ليس في روم صوتي حالياً!", ephemeral=True)
        return
    await member.edit(deafen=True, reason=reason)
    await interaction.response.send_message(f"🔇 تم إصمام العضو {member.mention} بنجاح.", ephemeral=True)

@bot.tree.command(name="timeout", description="إعطاء تايم آوت (ميوت كتابي) لعضو لفترة معينة")
@app_commands.default_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "بدون سبب"):
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await interaction.response.send_message(f"⏳ تم إعطاء تايم آوت للعضو {member.mention} لمدة {minutes} دقيقة.", ephemeral=True)

@bot.tree.command(name="kick", description="طرد عضو من السيرفر (للإدارة العليا)")
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 تم طرد العضو {member.mention} من السيرفر بنجاح.", ephemeral=True)

@bot.tree.command(name="ban", description="حظر عضو من السيرفر نهائياً (للإدارة العليا)")
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 تم حظر العضو {member.mention} من السيرفر بنجاح.", ephemeral=True)


# ==================== 💰 نظام الاقتصاد ====================

@bot.tree.command(name="balance", description="عرض رصيدك من العملات")
async def balance(interaction: discord.Interaction):
    uid = interaction.user.id
    bal = user_balances.get(uid, 100)
    embed = discord.Embed(title="💰 رصيدك المالي", description=f"لديك **{bal}** عملة في محفظتك 🪙", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="daily", description="استلام المكافأة اليومية")
async def daily(interaction: discord.Interaction):
    uid = interaction.user.id
    current = user_balances.get(uid, 100)
    user_balances[uid] = current + 500
    embed = discord.Embed(title="🎁 المكافأة اليومية", description="تم إضافة **500** عملة إلى رصيدك بنجاح! 💸", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)


# ==================== 👥 الأعضاء والمساعدة ====================

@bot.tree.command(name="ping", description="عرض سرعة استجابة Fynex Bot")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="🏓 سرعة استجابة Fynex Bot", description=f"⚡ السرعة: **{latency}ms**", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="عرض جميع أوامر Fynex Bot")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🌟 قائمة أوامر Fynex Bot الشاملة", description="جميع الأوامر تعمل بنظام Slash Commands:", color=discord.Color.dark_embed())
    embed.add_field(name="🎮 الألعاب", value="`-روليت` (للإداريين)", inline=False)
    embed.add_field(name="🛡️ الإدارة والحمايات", value="`/protections` - `/toggle_protection` - `/clear` - `/lock` - `/unlock`", inline=False)
    embed.add_field(name="🛠️ الإدارة الصوتية والكتابية", value="`/mute` - `/unmute` - `/move` - `/deafen` - `/timeout`", inline=False)
    embed.add_field(name="⚖️ الرتب العليا (الإدارة العليا)", value="`/kick` - `/ban`", inline=False)
    embed.add_field(name="💰 الاقتصاد والأعضاء", value="`/balance` - `/daily` - `/ping` - `/help`", inline=False)
    embed.set_footer(text="Fynex Bot Ultimate System")
    await interaction.response.send_message(embed=embed)

bot.run(os.getenv('TOKEN'))
