from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telethon.sync import TelegramClient

API_ID = 34781021
API_HASH = "be4e092a72583bbe9c938ab614924070"
PHONE_NUMBER = "+972567238399"
BOT_TOKEN = "8687994922:AAF8VSOMQqM7rd2o5R1GhQCDaCe-JfF-Wa8"

CHANNELS = ["eisaaq","darkwaves8","Ahmed_OmarFx","SOLOM_FX","blackforex24"]
BUY_WORDS = ["شراء","buy","long","صعود","ارتفاع"]
SELL_WORDS = ["بيع","sell","short","هبوط","انخفاض"]

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ جاري التحليل...")
    buy, sell = 0, 0
    with TelegramClient("session", API_ID, API_HASH) as client:
        for ch in CHANNELS:
            msgs = client.get_messages(ch, limit=20)
            for m in msgs:
                if m.text:
                    t = m.text.lower()
                    if any(w in t for w in BUY_WORDS): buy += 1
                    if any(w in t for w in SELL_WORDS): sell += 1
    total = buy + sell
    if total:
        bp = round(buy/total*100)
        sp = round(sell/total*100)
        bias = "🟢 BULLISH" if bp > sp else "🔴 BEARISH"
        await update.message.reply_text(f"📊 النتيجة:\n🟢 شراء: {bp}%\n🔴 بيع: {sp}%\n{bias}")
    else:
        await update.message.reply_text("ما لقيت توصيات!")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("analyze", analyze))
app.run_polling()
