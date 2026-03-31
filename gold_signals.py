"""
Gold Trading Signal Analyzer using Telethon
============================================
Reads the last 20 messages from specified Telegram public channels and
analyzes them for gold (XAUUSD) buy/sell signals.

SETUP REQUIRED:
1. Go to https://my.telegram.org and log in
2. Click "API development tools"
3. Create a new application to get your API_ID and API_HASH
4. Fill in API_ID, API_HASH, and PHONE_NUMBER below
"""

import asyncio
import re
from telethon import TelegramClient
from telethon.tl.types import Message

API_ID = 34781021          # <-- Replace with your API ID (integer)
API_HASH = "be4e092a72583bbe9c938ab614924070"        # <-- Replace with your API Hash (string)
PHONE_NUMBER = "+972567238399"    # <-- Replace with your phone number (e.g. "+123456789")

CHANNELS = [
    "eisaaq",
    "darkwaves8",
    "Ahmed_OmarFx",
    "SOLOM_FX",
    "blackforex24",
]

MESSAGES_PER_CHANNEL = 20

BUY_KEYWORDS = [
    "شراء",
    "buy",
    "long",
    "صعود",
    "ارتفاع",
]

SELL_KEYWORDS = [
    "بيع",
    "sell",
    "short",
    "هبوط",
    "انخفاض",
]


def contains_keyword(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    for kw in keywords:
        pattern = rf"\b{re.escape(kw.lower())}\b"
        if re.search(pattern, text_lower):
            return True
    return False


def classify_message(text: str) -> str | None:
    is_buy = contains_keyword(text, BUY_KEYWORDS)
    is_sell = contains_keyword(text, SELL_KEYWORDS)

    if is_buy and is_sell:
        return "mixed"
    elif is_buy:
        return "buy"
    elif is_sell:
        return "sell"
    return None


async def analyze_channels():
    client = TelegramClient("gold_session", API_ID, API_HASH)

    await client.start(phone=PHONE_NUMBER)
    print("Connected to Telegram\n")
    print("=" * 60)

    total_buy = 0
    total_sell = 0
    total_mixed = 0
    total_neutral = 0
    total_messages = 0

    for channel in CHANNELS:
        channel_buy = 0
        channel_sell = 0
        channel_mixed = 0
        channel_neutral = 0
        messages_fetched = 0

        print(f"\nChannel: @{channel}")
        print("-" * 40)

        try:
            entity = await client.get_entity(channel)
            async for message in client.iter_messages(entity, limit=MESSAGES_PER_CHANNEL):
                if not isinstance(message, Message) or not message.text:
                    continue

                messages_fetched += 1
                signal = classify_message(message.text)

                if signal == "buy":
                    channel_buy += 1
                    print(f"  [BUY]     {message.text[:80].strip()!r}")
                elif signal == "sell":
                    channel_sell += 1
                    print(f"  [SELL]    {message.text[:80].strip()!r}")
                elif signal == "mixed":
                    channel_mixed += 1
                    print(f"  [MIXED]   {message.text[:80].strip()!r}")
                else:
                    channel_neutral += 1

            channel_total = channel_buy + channel_sell + channel_mixed + channel_neutral
            signal_total = channel_buy + channel_sell + channel_mixed

            if signal_total > 0:
                buy_pct = channel_buy / signal_total * 100
                sell_pct = channel_sell / signal_total * 100
                mixed_pct = channel_mixed / signal_total * 100
            else:
                buy_pct = sell_pct = mixed_pct = 0.0

            print(f"\n  Messages scanned : {channel_total}")
            print(f"  Signal messages  : {signal_total}")
            print(f"  Buy signals      : {channel_buy}  ({buy_pct:.1f}%)")
            print(f"  Sell signals     : {channel_sell}  ({sell_pct:.1f}%)")
            print(f"  Mixed signals    : {channel_mixed}  ({mixed_pct:.1f}%)")

            total_buy += channel_buy
            total_sell += channel_sell
            total_mixed += channel_mixed
            total_neutral += channel_neutral
            total_messages += channel_total

        except Exception as e:
            print(f"  ERROR: Could not read @{channel}: {e}")

    print("\n" + "=" * 60)
    print("OVERALL SUMMARY — ALL CHANNELS")
    print("=" * 60)

    grand_signal_total = total_buy + total_sell + total_mixed

    if grand_signal_total > 0:
        grand_buy_pct = total_buy / grand_signal_total * 100
        grand_sell_pct = total_sell / grand_signal_total * 100
        grand_mixed_pct = total_mixed / grand_signal_total * 100
    else:
        grand_buy_pct = grand_sell_pct = grand_mixed_pct = 0.0

    print(f"Total messages scanned : {total_messages}")
    print(f"Total signal messages  : {grand_signal_total}")
    print(f"Total buy signals      : {total_buy}  ({grand_buy_pct:.1f}%)")
    print(f"Total sell signals     : {total_sell}  ({grand_sell_pct:.1f}%)")
    print(f"Total mixed signals    : {total_mixed}  ({grand_mixed_pct:.1f}%)")

    if grand_signal_total > 0:
        print("\n--- SIGNAL DIRECTION ---")
        if grand_buy_pct > grand_sell_pct:
            print(f"Overall bias: BULLISH (Buy {grand_buy_pct:.1f}% vs Sell {grand_sell_pct:.1f}%)")
        elif grand_sell_pct > grand_buy_pct:
            print(f"Overall bias: BEARISH (Sell {grand_sell_pct:.1f}% vs Buy {grand_buy_pct:.1f}%)")
        else:
            print("Overall bias: NEUTRAL (Buy and Sell signals are equal)")

    await client.disconnect()


if __name__ == "__main__":
    if API_ID == 0 or not API_HASH or not PHONE_NUMBER:
        print("ERROR: Please fill in API_ID, API_HASH, and PHONE_NUMBER at the top of the script.")
        print("Get your credentials at: https://my.telegram.org")
    else:
        asyncio.run(analyze_channels())
