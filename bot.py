import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory data stores
user_data = {}  # Stores user info
available_tasks = {}  # Format: {"Task name": "https://link.com"}

# Fetch your bot's token and admin ID directly from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Ensure you've set this environment variable
ADMIN_ID = os.getenv("ADMIN_ID")  # Ensure you've set this environment variable

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_data:
        user_data[user_id] = {
            "points": 0,
            "payout_info": None,
            "withdrawals": [],
            "referrer": None,
            "referred": []
        }

        if context.args:
            try:
                ref_id = int(context.args[0])
                if ref_id != user_id and ref_id in user_data:
                    user_data[user_id]["referrer"] = ref_id
                    user_data[ref_id]["points"] += 100
                    user_data[ref_id]["referred"].append(user_id)
                    await update.message.reply_text(
                        f"🎉 Referral successful! {ref_id} earned 100 points."
                    )
            except:
                pass

        referral_link = f"https://t.me/{update.effective_chat.username}?start={user_id}"
        await update.message.reply_text(
            f"👋 You’ve been registered successfully.\n\nYour referral link: {referral_link}"
        )
    else:
        await update.message.reply_text("✅ You’re already registered.")

# /balance command
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = user_data.get(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ You are not registered.")
        return
    await update.message.reply_text(f"💰 Your balance: {user['points']} points")

# /set_payout (wallet or bank)
async def set_payout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = user_data.get(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ You are not registered.")
        return
    payout_info = " ".join(context.args)
    if not payout_info:
        await update.message.reply_text("❌ Please provide your wallet or bank account.")
        return
    user["payout_info"] = payout_info
    await update.message.reply_text(f"✅ Payout info saved: {payout_info}")

# /available_tasks
async def available_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not available_tasks:
        await update.message.reply_text("📭 No tasks available.")
        return
    msg = "📋 Available Tasks:\n\n"
    for i, (task, link) in enumerate(available_tasks.items(), start=1):
        msg += f"{i}. {task} - {link}\n"
    await update.message.reply_text(msg)

# /complete_task <task_number>
async def complete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = user_data.get(user_id)
    if not user:
        await update.message.reply_text("❌ You are not registered.")
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /complete_task <task_number>")
        return
    try:
        task_num = int(context.args[0]) - 1
        task_list = list(available_tasks.items())
        if 0 <= task_num < len(task_list):
            task_name, task_link = task_list[task_num]
            user["points"] += 100
            await update.message.reply_text(
                f"✅ Task completed: {task_name}\nYou earned 100 points!"
            )
        else:
            await update.message.reply_text("❌ Invalid task number.")
    except ValueError:
        await update.message.reply_text("❌ Task number must be a number.")

# /request_withdrawal
async def request_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = user_data.get(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ You are not registered.")
        return
    if user["points"] < 4000:
        await update.message.reply_text("❌ You need at least 4000 points to withdraw.")
        return
    if not user["payout_info"]:
        await update.message.reply_text("❌ Please set your wallet or bank info first using /set_payout")
        return
    withdrawal_amount = user["points"]
    user["withdrawals"].append({"amount": withdrawal_amount})
    user["points"] = 0
    await update.message.reply_text(f"💸 Withdrawal successful for {withdrawal_amount} points.")

# /referral_history
async def referral_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = user_data.get(update.effective_user.id)
    if not user or not user["referred"]:
        await update.message.reply_text("📭 No referral history.")
        return
    msg = "📜 Referral History:\n"
    for i, uid in enumerate(user["referred"], 1):
        msg += f"{i}. User ID: {uid}\n"
    await update.message.reply_text(msg)

# /admin_panel
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("❌ Admin access only.")
        return
    msg = "👨‍💼 Admin Panel:\n\n"
    for uid, user in user_data.items():
        msg += (
            f"User: {uid}\nPoints: {user['points']}\n"
            f"Payout Info: {user['payout_info']}\n"
            f"Referrals: {user['referred']}\n\n"
        )
    await update.message.reply_text(msg)

# /add_task "task name" url
async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("❌ Admin only.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /add_task \"Task Name\" <URL>")
        return
    task_name = context.args[0]
    task_link = context.args[1]
    available_tasks[task_name] = task_link
    await update.message.reply_text(f"✅ Task added: {task_name} - {task_link}")

# /credit_user <user_id> <points>
async def credit_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("❌ Admin only.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /credit_user <user_id> <points>")
        return
    try:
        target_id = int(context.args[0])
        points = int(context.args[1])
        if target_id in user_data:
            user_data[target_id]["points"] += points
            await update.message.reply_text(f"✅ {points} points credited to user {target_id}.")
        else:
            await update.message.reply_text("❌ User not found.")
    except:
        await update.message.reply_text("❌ Invalid input.")

# Bot start function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("set_payout", set_payout))
    app.add_handler(CommandHandler("available_tasks", available_tasks_command))
    app.add_handler(CommandHandler("complete_task", complete_task))
    app.add_handler(CommandHandler("request_withdrawal", request_withdrawal))
    app.add_handler(CommandHandler("referral_history", referral_history))
    app.add_handler(CommandHandler("admin_panel", admin_panel))
    app.add_handler(CommandHandler("add_task", add_task))
    app.add_handler(CommandHandler("credit_user", credit_user))

    app.run_polling()

if __name__ == "__main__":
    main()
