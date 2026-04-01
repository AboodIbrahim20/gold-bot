"""
Gold Trading Signal Bot
=======================
Reads the last 20 messages from specified Telegram public channels and
analyzes them for gold (XAUUSD) buy/sell signals.

Send /analyze to the bot to receive buy/sell percentages and overall market bias.

SETUP:
  BOT_TOKEN   → @BotFather on Telegram (/newbot)
  API_ID      → https://my.telegram.org → API development tools
  API_HASH    → same page as above
  PHONE_NUMBER→ your Telegram phone number e.g. "+1234567890"
"""

import logging
import re

from telethon import TelegramClient
from telethon.tl.types import Message
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN    = ""                                    # <-- Paste your BotFather token here
API_ID       = 34781021
API_HASH     = "be4e092a72583bbe9c938ab614924070"
PHONE_NUMBER = "+972567238399"

CHANNELS = [
    "eisaaq",
    "darkwaves8",
    "Ahmed_OmarFx",
    "SOLOM_FX",
    "blackforex24",
]

MESSAGES_PER_CHANNEL = 20

BUY_KEYWORDS  = ["شراء", "buy", "long", "صعود", "ارتفاع"]
SELL_KEYWORDS = ["بيع", "sell", "short", "هبوط", "انخفاض"]


def contains_keyword(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw.lower())}\b", text_lower):
            return True
    return False


def classify_message(text: str) -> str | None:
    is_buy  = contains_keyword(text, BUY_KEYWORDS)
    is_sell = contains_keyword(text, SELL_KEYWORDS)
    if is_buy and is_sell:
        return "mixed"
    if is_buy:
        return "buy"
    if is_sell:
        return "sell"
    return None


async def fetch_signals() -> dict:
    """
    Read channels via Telethon and return signal counts.
    Uses 'async with' so it works correctly inside an already-running event loop.
    """
    results = []
    total = {"buy": 0, "sell": 0, "mixed": 0, "neutral": 0, "messages": 0}

    # Fix: use 'async with' instead of client.start() / client.disconnect()
    # This is required when running inside python-telegram-bot's event loop.
    async with TelegramClient("gold_session", API_ID, API_HASH) as client:
        await client.start(phone=PHONE_NUMBER)

        for channel in CHANNELS:
            counts = {
                "buy": 0, "sell": 0, "mixed": 0,
                "neutral": 0, "messages": 0, "error": None,
            }
            try:
                entity = await client.get_entity(channel)
                async for msg in client.iter_messages(entity, limit=MESSAGES_PER_CHANNEL):
                    if not isinstance(msg, Message) or not msg.text:
                        continue
                    counts["messages"] += 1
                    signal = classify_message(msg.text)
                    counts[signal or "neutral"] += 1

            except Exception as e:
                counts["error"] = str(e)
                logger.warning("Could not read @%s: %s", channel, e)

            results.append({"channel": channel, **counts})
            for key in ("buy", "sell", "mixed", "neutral", "messages"):
                total[key] += counts[key]

    return {"channels": results, "total": total}


def build_reply(data: dict) -> str:
    lines = ["📊 *Gold Trading Signal Analysis*\n"]
    lines.append(f"Channels scanned: {len(data['channels'])}")
    lines.append(f"Messages per channel: {MESSAGES_PER_CHANNEL}\n")

    for ch in data["channels"]:
        name = ch["channel"]
        if ch["error"]:
            lines.append(f"@{name}: ❌ {ch['error']}")
            continue

        signal_total = ch["buy"] + ch["sell"] + ch["mixed"]
        buy_pct  = ch["buy"]  / signal_total * 100 if signal_total else 0.0
        sell_pct = ch["sell"] / signal_total * 100 if signal_total else 0.0

        lines.append(
            f"@{name} ({ch['messages']} msgs)\n"
            f"  🟢 Buy: {ch['buy']} ({buy_pct:.0f}%)"
            f"  🔴 Sell: {ch['sell']} ({sell_pct:.0f}%)"
            f"  🟡 Mixed: {ch['mixed']}"
        )

    t            = data["total"]
    grand_signal = t["buy"] + t["sell"] + t["mixed"]

    lines.append("\n─────────────────────")
    lines.append("*Overall Summary*")
    lines.append(f"Total messages: {t['messages']}")
    lines.append(f"Signal messages: {grand_signal}")

    if grand_signal > 0:
        buy_pct  = t["buy"]   / grand_signal * 100
        sell_pct = t["sell"]  / grand_signal * 100
        mix_pct  = t["mixed"] / grand_signal * 100
        lines.append(f"🟢 Buy:   {t['buy']} ({buy_pct:.1f}%)")
        lines.append(f"🔴 Sell:  {t['sell']} ({sell_pct:.1f}%)")
        lines.append(f"🟡 Mixed: {t['mixed']} ({mix_pct:.1f}%)")
        lines.append("")
        if buy_pct > sell_pct:
            lines.append(f"📈 *Bias: BULLISH* — Buy {buy_pct:.1f}% vs Sell {sell_pct:.1f}%")
        elif sell_pct > buy_pct:
            lines.append(f"📉 *Bias: BEARISH* — Sell {sell_pct:.1f}% vs Buy {buy_pct:.1f}%")
        else:
            lines.append("⚖️ *Bias: NEUTRAL* — Equal buy and sell signals")
    else:
        lines.append("No trading signals found in recent messages.")

    return "\n".join(lines)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Welcome to the Gold Signal Bot!\n\n"
        "Send /analyze to scan Telegram channels for gold trading signals "
        "and get buy/sell percentages with an overall market bias."
    )


async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔍 Analyzing channels, please wait...")
    try:
        data  = await fetch_signals()
        reply = build_reply(data)
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.exception("Error during analysis")
        await update.message.reply_text(f"❌ Error: {e}")


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("analyze", cmd_analyze))
    logger.info("Bot is running. Send /analyze to your bot on Telegram.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    if not BOT_TOKEN:
        print(
            "ERROR: BOT_TOKEN is empty.\n"
            "  1. Message @BotFather on Telegram\n"
            "  2. Send /newbot and follow the steps\n"
            "  3. Paste the token into BOT_TOKEN at the top of this file"
        )
    else:
        main()
