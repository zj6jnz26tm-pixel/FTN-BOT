
import os
import random
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# رقم الآي دي الخاص بروم ai الذي أرسلته
AI_CHANNEL_ID = 1567709659974860860

GENERAL_RESPONSES = [
    "يا هلا! أنا معك، اسأل اللي بخاطرك وأنا أخوك في روم الـ AI ✨",
    "صدقت! عاد علمنا، وش وديان السوالف اليوم في سيرفر FTN؟",
    "ممم.. نقطة مهمة! شاركنا تفاصيل أكثر عشان نفيدك أكثر يا غالي.",
    "أنا حاضر وموجود طوال الوقت، تفضل اطرح سؤالك أو موضوعك!",
    "الله يقويك! كيف أقدر أساعدك بهذا الخصوص؟",
    "يا سلام عليك! اسأل اللي تبيه، كلنا كذا جاهزين لخدمتك.",
    "جميل جداً! أنا أسمعك، كمل وش عندك؟",
    "حلوة الفكرة! بس لو توضح لي أكثر، أكون عاجز عن الشكر في مساعدتك."
]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_message(message):
    # 1. منع البوت من الرد على نفسه
    if message.author.bot:
        return

    # 2. حصر التفاعل فقط داخل روم الـ AI المحدد بالآي دي
    if message.channel.id != AI_CHANNEL_ID:
        await bot.process_commands(message)
        return

    # 3. تجاهل الأوامر التي تبدأ بـ !
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return

    # 4. الرد العشوائي على أي رسالة داخل روم الـ ai فقط
    reply_text = random.choice(GENERAL_RESPONSES)
    await message.reply(reply_text)

    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! 🏓 البوت شغال وسريع جداً.')

bot.run(os.getenv('TOKEN'))
