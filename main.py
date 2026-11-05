
import os
import random
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class FTNBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands successfully for FTN-BOT.")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

bot = FTNBot()

AI_CHANNEL_ID = 1567709659974860860

GENERAL_RESPONSES = [
    "يا هلا! أنا معك، اسأل اللي بخاطرك وأنا أخوك في روم الـ AI ✨",
    "صدقت! عاد علمنا، وش وديان السوالف اليوم في سيرفر FTN؟",
    "ممم.. نقطة مهمة! شاركنا تفاصيل أكثر عشان نفيدك أكثر يا غالي.",
    "أنا حاضر وموجود طوال الوقت، تفضل اطرح سؤالك أو موضوعك!",
    "الله يقويك! كيف أقدر أساعدك بهذا الخصوص؟",
    "يا سلام عليك! اسأل اللي تبيه، كلنا كذا جاهزين لخدمتك."
]

user_balances = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} | FTN-BOT Online 🚀')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # نظام الأوامر النصية العادية (مثل -روليت) الحصري للإداريين
    if message.content.startswith('-روليت') or message.content.startswith('-roulette'):
        # التحقق من صلاحيات الإدارة (مثلاً إدارة الرسائل أو الرتب)
        if not message.author.guild_permissions.manage_guild:
            await message.reply("❌ عذراً يا غالي، هذا الأمر مخصص للإداريين فقط!", delete_after=5)
            return

        view = RouletteView()
        embed = discord.Embed(
            title="🎰 سحب روليت FTN",
            description="سوف تبدأ لعبه روليت اضغط الزر للمشاركه ⏳ (لديك 30 ثانية)",
            color=discord.Color.gold()
        )
        embed.set_footer(text="FTN-BOT Events")
        
        sent_msg = await message.channel.send(embed=embed, view=view)

        # الانتظار لمدة 30 ثانية لتسجيل اللاعبين
        import asyncio
        await asyncio.sleep(30)

        if not view.participants:
            embed.description = "❌ انتهى الوقت ولم يشارك أحد في الروليت!"
            await sent_msg.edit(embed=embed, view=None)
            return

        # اختيار الفائز عشوائياً
        winner = random.choice(view.participants)
        
        win_embed = discord.Embed(
            title="🎉 إعلان فائز الروليت",
            description=f"وقع الاختيار على ({winner.mention}) مبروك الفوز يا وحش! 🏆",
            color=discord.Color.green()
        )
        win_embed.set_thumbnail(url=winner.display_avatar.url)
        win_embed.set_footer(text="FTN-BOT Roulette Winner")

        await sent_msg.edit(embed=win_embed, view=None)
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


# ==================== 🛡️ نظام الإدارة والأوامر ====================

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

@bot.tree.command(name="ping", description="عرض سرعة استجابة بوت FTN")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="🏓 سرعة استجابة بوت FTN", description=f"⚡ السرعة: **{latency}ms**", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="عرض جميع أوامر بوت FTN")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🌟 قائمة أوامر بوت FTN الشاملة", description="جميع الأوامر تعمل بنظام Slash Commands (-) باستثناء الروليت الإداري:", color=discord.Color.dark_embed())
    embed.add_field(name="🎮 الألعاب", value="`-روليت` (للإداريين) - `/games` - `/rps` - `/guess`", inline=False)
    embed.add_field(name="🛡️ الإدارة", value="`/clear` - `/lock` - `/unlock`", inline=False)
    embed.add_field(name="💰 الاقتصاد", value="`/balance` - `/daily`", inline=False)
    embed.add_field(name="👥 الأعضاء", value="`/ping` - `/help`", inline=False)
    embed.set_footer(text="FTN-BOT Ultimate System")
    await interaction.response.send_message(embed=embed)

bot.run(os.getenv('TOKEN'))
