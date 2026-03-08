import os
import json
import requests
import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================= CONFIG ================= #

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API = os.getenv("GROQ_API")

ADMIN_ID = 6919025708
GROUP_USERNAME = "@dark_princes12"
CHANNEL_USERNAME = "@myfirstchannel12"
FREE_LIMIT = 10
PAYMENT_NUMBER = "01309924182"

DB_FILE = "database.json"

# ================= DATABASE ================= #

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# ================= MEMBERSHIP CHECK ================= #

async def check_membership(user_id, context):
    try:
        g = await context.bot.get_chat_member(GROUP_USERNAME, user_id)
        c = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        valid = ["member", "administrator", "creator"]
        return g.status in valid and c.status in valid
    except:
        return False

async def force_subscribe(update, context):
    keyboard = [
        [InlineKeyboardButton("📢 Join Group", url="https://t.me/dark_princes12")],
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/myfirstchannel12")],
        [InlineKeyboardButton("✅ Verify", callback_data="verify")]
    ]

    await update.message.reply_text(
        "🚫 Join Group & Channel First!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def verify_callback(update, context):
    query = update.callback_query
    await query.answer()
    ok = await check_membership(query.from_user.id, context)
    if ok:
        await query.edit_message_text("✅ Verified! Send your message.")
    else:
        await query.answer("❌ Not joined yet!", show_alert=True)

# ================= COMMANDS ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 BD Ultra AI Bot (Free Groq AI)\n\n"
        "10 Free messages daily\n"
        "Use /buy for premium"
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💎 Premium Plans:\n\n"
        f"7 Days = 49৳\n"
        f"30 Days = 149৳\n"
        f"90 Days = 399৳\n\n"
        f"Send Payment to:\n{PAYMENT_NUMBER}\n"
        f"(Bkash/Nagad/Rocket)"
    )

# ================= CHAT ================= #

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()

    if user_id not in db:
        db[user_id] = {"premium": False, "used": 0}

    # Free verification
    if not db[user_id]["premium"]:
        verified = await check_membership(update.effective_user.id, context)
        if not verified:
            await force_subscribe(update, context)
            return

        if db[user_id]["used"] >= FREE_LIMIT:
            await update.message.reply_text("❌ Free limit finished.")
            return

    # ================= GROQ API ================= #

    headers = {
        "Authorization": f"Bearer {GROQ_API}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "user", "content": update.message.text}
        ],
        "temperature": 0.7
    }

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )

        print("Status:", r.status_code)
        print("Response:", r.text)

        if r.status_code == 200:
            result = r.json()
            reply = result["choices"][0]["message"]["content"]
        elif r.status_code == 401:
            reply = "❌ Invalid Groq API Key."
        else:
            reply = f"⚠️ Groq API Error ({r.status_code})"

    except Exception as e:
        print("ERROR:", str(e))
        reply = "⚠️ AI Connection Failed."

    db[user_id]["used"] += 1
    save_db(db)

    await update.message.reply_text(reply)

# ================= MAIN ================= #

print("🔥 BD Ultra AI Bot Running (Groq Free Mode)...")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
app.add_handler(CallbackQueryHandler(verify_callback, pattern="verify"))

app.run_polling()
