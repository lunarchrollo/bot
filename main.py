from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackContext,
    CallbackQueryHandler, MessageHandler, ContextTypes,
    filters
)
from db import Session, User, Task
from utils import get_or_create_user
import os

BOT_TOKEN = os.environ.get("7876356454:AAGUWe6WWUcWLy9E4CrkuamXzU1K1uFarNg")
ADMIN_IDS = [1489701727]  # Replace with your Telegram ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ref_id = context.args[0] if context.args else None
    ref_id = int(ref_id) if ref_id and ref_id.isdigit() else None
    user = get_or_create_user(update.effective_user.id, ref_id)
    await update.message.reply_text(
        "Welcome to Task Bot!\nBalance: $0.00",
        reply_markup=main_menu()
    )

def main_menu():
    buttons = [
        [InlineKeyboardButton("Set Country", callback_data="set_country")],
        [InlineKeyboardButton("Tasks", callback_data="tasks")],
        [InlineKeyboardButton("Referral", callback_data="referral")],
        [InlineKeyboardButton("Set Wallet", callback_data="set_wallet")],
        [InlineKeyboardButton("Withdraw", callback_data="withdraw")]
    ]
    return InlineKeyboardMarkup(buttons)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    session = Session()
    user = session.query(User).filter_by(telegram_id=user_id).first()

    if query.data == "set_country":
        await query.message.reply_text("Send your country name:")
        context.user_data['awaiting_country'] = True

    elif query.data == "tasks":
        tasks = session.query(Task).all()
        completed = user.tasks_done or []
        available = [t for t in tasks if t.id not in completed]
        if not available:
            await query.message.reply_text("No new tasks right now.")
        else:
            for t in available:
                btn = InlineKeyboardButton("Do Task", url=t.url)
                done_btn = InlineKeyboardButton("Mark as Done", callback_data=f"done_{t.id}")
                markup = InlineKeyboardMarkup([[btn], [done_btn]])
                await query.message.reply_text(f"**{t.title}**", reply_markup=markup)

    elif query.data == "referral":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.message.reply_text(f"Your referral link:\n{ref_link}\nEarn 10% of your referrals' task earnings.")

    elif query.data == "set_wallet":
        await query.message.reply_text("Send your wallet like this:\n`BTC: your_address`\n`PayPal: your_email`")
        context.user_data['awaiting_wallet'] = True

    elif query.data == "withdraw":
        if user.balance >= 50:
            await query.message.reply_text("Withdrawal requested. Admin will review it.")
            # Notify admin
        else:
            await query.message.reply_text("Minimum withdrawal amount is $50.")

    session.close()

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
    text = update.message.text

    if context.user_data.get('awaiting_country'):
        user.country = text
        session.commit()
        await update.message.reply_text("Country set!")
        context.user_data['awaiting_country'] = False

    elif context.user_data.get('awaiting_wallet'):
        try:
            wtype, addr = text.split(":", 1)
            wallet = user.wallet or {}
            wallet[wtype.strip().upper()] = addr.strip()
            user.wallet = wallet
            session.commit()
            await update.message.reply_text("Wallet updated!")
        except:
            await update.message.reply_text("Invalid format. Try again.")
        context.user_data['awaiting_wallet'] = False

    session.close()

async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    task_id = int(query.data.split("_")[1])

    session = Session()
    user = session.query(User).filter_by(telegram_id=user_id).first()
    if task_id in (user.tasks_done or []):
        await query.answer("Already completed.")
    else:
        user.tasks_done = (user.tasks_done or []) + [task_id]
        user.balance += 0.10
        # Referral bonus
        if user.referrer_id:
            ref = session.query(User).filter_by(telegram_id=user.referrer_id).first()
            if ref:
                ref.balance += 0.01
                ref.referral_earnings += 0.01
        session.commit()
        await query.message.reply_text("Task marked as done! +$0.10")
    session.close()

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You're not authorized.")
        return
    try:
        title, link = update.message.text.split("|", 1)
        task = Task(title=title.strip(), url=link.strip())
        session = Session()
        session.add(task)
        session.commit()
        session.close()
        await update.message.reply_text("Task added!")
    except:
        await update.message.reply_text("Format: /addtask Task title | https://link.com")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addtask", add_task))
app.add_handler(CallbackQueryHandler(button_handler, pattern="^(?!done_).*"))
app.add_handler(CallbackQueryHandler(mark_done, pattern="^done_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

if __name__ == "__main__":
    app.run_polling()
