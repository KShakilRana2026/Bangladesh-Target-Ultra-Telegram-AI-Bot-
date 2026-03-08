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

# ================== CONFIG ================== #

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API = os.getenv("DEEPSEEK_API")

ADMIN_ID = 6919025708
GROUP_USERNAME = "@dark_princes12"
CHANNEL_USERNAME = "@myfirstchannel12"
FREE_LIMIT = 10
PAYMENT_NUMBER = "01309924182"

DB_FILE = "database.json"

# ================== DATABASE ================== #

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# ================== MEMBERSHIP CHECK ================== #

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
        "🚫 You must join our Group & Channel first!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def verify_callback(update, context):
    query = update.callback_query
    await query.answer()
    ok = await check_membership(query.from_user.id, context)
    if ok:
        await query.edit_message_text("✅ Verification Successful! Now send your message.")
    else:
        await query.answer("❌ Still not joined!", show_alert=True)

# ================== COMMANDS ================== #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Welcome to BD Ultra AI Bot!\n\n"
        "Free: 10 messages daily\n"
        "Use /buy for premium"
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💎 Premium Plans:\n\n"
        f"7 Days = 49৳\n"
        f"30 Days = 149৳\n"
        f"90 Days = 399৳\n\n"
        f"Send Payment to:\n{PAYMENT_NUMBER}\n"
        f"(Bkash/Nagad/Rocket)\n\n"
        f"Then send screenshot to admin."
    )

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /approve user_id days")
        return

    user_id = context.args[0]
    days = int(context.args[1])

    db = load_db()
    expire = datetime.datetime.now() + datetime.timedelta(days=days)

    db[user_id] = {
        "premium": True,
        "expire": expire.isoformat(),
        "used": 0
    }

    save_db(db)
    await update.message.reply_text("✅ User Approved!")

# ================== CHAT SYSTEM ================== #

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()

    if user_id not in db:
        db[user_id] = {"premium": False, "used": 0}

    # Expiry check
    if db[user_id]["premium"]:
        expire = datetime.datetime.fromisoformat(db[user_id]["expire"])
        if datetime.datetime.now() > expire:
            db[user_id]["premium"] = False

    # Free verification
    if not db[user_id]["premium"]:
        verified = await check_membership(update.effective_user.id, context)
        if not verified:
            await force_subscribe(update, context)
            return

        if db[user_id]["used"] >= FREE_LIMIT:
            await update.message.reply_text("❌ Free limit finished. Use /buy")
            return

    # ================= AI CALL ================= #

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": update.message.text}
        ]
    }

    try:
        r = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )

        if r.status_code == 200:
            result = r.json()
            reply = result["choices"][0]["message"]["content"]
        elif r.status_code == 401:
            reply = "❌ Invalid DeepSeek API Key."
        else:
            reply = f"⚠️ API Error ({r.status_code})"

    except Exception as e:
        reply = "⚠️ AI Connection Failed."

    db[user_id]["used"] += 1
    save_db(db)

    await update.message.reply_text(reply)

# ================== MAIN ================== #

print("🔥 BD Ultra AI Bot Running (Polling Mode)...")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(CommandHandler("approve", approve))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
app.add_handler(CallbackQueryHandler(verify_callback, pattern="verify"))

app.run_polling()
