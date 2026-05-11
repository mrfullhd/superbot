from telegram import Update
from telegram.ext import ContextTypes
from core.downloader import download_manager

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📝 `/cancel ID`\nشناسه دانلود را وارد کنید")
        return
    
    download_id = int(context.args[0])
    user_id = update.effective_user.id
    
    if download_manager.cancel_download(user_id, download_id):
        await update.message.reply_text("🚫 دانلود لغو شد.")
    else:
        await update.message.reply_text("⚠️ دانلود یافت نشد یا قبلاً لغو شده.")

async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data  # cancel_ID
    
    download_id = int(data.replace("cancel_", ""))
    user_id = update.effective_user.id
    
    if download_manager.cancel_download(user_id, download_id):
        await query.answer("دانلود لغو شد")
        await query.edit_message_text("🚫 دانلود لغو شد.")
    else:
        await query.answer("قبلاً لغو شده")
