import os
import random
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# قوائم الردود المتنوعة والعشوائية لكل حالة
GREETINGS = [
    "هلا والله يا غالي! منور السيرفر، كيف أقدر أخدمك اليوم؟ ✨",
    "وعليكم السلام ورحمة الله! أهلاً بك يا {author}، عسى أمورك كلها طيبة؟",
    "أهلاً وسهلاً! حياك الله، وش عندنا اليوم من سوالف أو طلبات؟",
    "مرحباً بك! أنا جاهز ومروق، اسأل اللي بخاطرك وأنا أخوك.",
    "يا هلا بالطيب! منورنا والله، كيف أقدر أساعدك في سيرفر FTN؟"
]

HOW_ARE_YOU = [
    "الحمد لله تمام التمام، جالس أراقب الشات وأساعد الشباب! أنت كيفك؟",
    "بأحسن حال دامكم منورين السيرفر! 🚀",
    "كل أموري تمام والوضع بالسليم، أنت بشرني عنك وعن أحوالك؟",
    "أنا بوت رايق ٢٤ ساعة ما أعرف التعب، عساك أنت مبسوط؟"
]

WHO_ARE_CON = [
    "أنا مساعدك الذكي والشخصية البرمجية هنا في سيرفر FTN، هدفنا نخليه أفضل سيرفر!",
    "أنا بوت السيرفر المعتمد، أجيب على استفساراتكم وأساعدكم بكل اللي تحتاجونه.",
    "أنا رفيقكم الرقمي، صمموني عشان أكون دايماً موجود وأخدمكم."
]

THANKS_REPLIES = [
    "العفو يا قلبي، ما سوينا الا الواجب! ❤️",
    "حبيبي والله، عيوننا لك وتحت أمرك بأي وقت!",
    "ولو! لا تشيل هم، حنا بالخدمة دايم ✨",
    "تسلم لي والله، متى ما احتجت شي أنا هنا."
]

JOKES = [
    "مرة واحد محشش سألوه: وش رايك في التحريات؟ قال: والله ما أعرفهم بس شكلهم أخلاق! 😂",
    "قلك واحد دخل مطعم وطلب غداء، قال له الگارسون: تحب سفرة ولا طيارة؟ قال: لا خليه قطار! 🚂",
    "فيه نملة حطت يدها على راسها ليه؟ تتذكر وين حطت سكر! 🐜",
    "واحد بخيل سألوه: لو صار بردان وش تسوي؟ قال: أقرب مندفة، سألوه: ولو زاد البرد؟ قال: أشغال البطانية! 🥶"
]

DEFAULT_RESPONSES = [
    "الله، سؤال جميل! بس صراحة ما فهمته بالضبط، عندك أوامر ثانية أقدر أساعدك فيها؟",
    "اهبط يا بطل ووضح لي أكثر عشان أقدر أجيبك زين! 🤔",
    "ممم... هذه جديدة علي! بس جرب تسألني سؤال ثاني أو اكتب !ping للاختبار.",
    "أنا جاهز لأي استفسار بس شكل مخي فصل في هذه النقطة، جرب صيغة ثانية!"
]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_message(message):
    # حماية صارمة من حلقة التكرار (منع البوت من الرد على نفسه)
    if message.author.bot:
        return

    content = message.content.lower().strip()
    author_mention = message.author.mention

    # 1. الترحيب والتحيات (يختار رد عشوائي)
    if any(w in content for w in ["السلام عليكم", "هلا", "مرحبا", "اهلين", "صباح", "مساء"]):
        reply_text = random.choice(GREETINGS).format(author=author_mention)
        await message.reply(reply_text)
        return

    # 2. السؤال عن الحال
    elif any(w in content for w in ["كيفك", "شخبارك", "وش اخبارك", "عساك بخير"]):
        await message.reply(random.choice(HOW_ARE_YOU))
        return

    # 3. من أنت
    elif any(w in content for w in ["من أنت", "وش تسوي", "مين انت", "اسمك"]):
        await message.reply(random.choice(WHO_ARE_CON))
        return

    # 4. الشكر
    elif any(w in content for w in ["شكرا", "مشكور", "يعطيك العافيه", "كفو", "تسلم"]):
        await message.reply(random.choice(THANKS_REPLIES))
        return

    # 5. نكت
    elif any(w in content for w in ["نكتة", "نكت", "ضحكني"]):
        await message.reply(random.choice(JOKES))
        return

    # 6. عند المنشن (يختار عشوائي من الردود العامة أو الترحيبية)
    elif bot.user.mentioned_in(message):
        await message.reply(f"عيوني يا {author_mention}! حاضر وموجود، اسأل باللي تبيه وأنا أجيبك.")
        return

    # 7. إذا كتب كلام عام غير معروف (يرد برد عشوائي مختلف عشان ما يكرر نفس الجملة)
    if not message.content.startswith('!'):
        # إذا تبغاه يرد على كل شي برد عشوائي فك التفعيل، أو اتركه للرسائل الموجهة
        pass

    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! 🏓 البوت شغال وسريع جداً.')

bot.run(os.getenv('TOKEN'))

if message.channel.name != "ai":
    await bot.process_commands(message)
    return
