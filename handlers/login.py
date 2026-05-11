from telegram import Update
from telegram.ext import ContextTypes
from core.google_auth import google_auth
from keyboards.inline import login_keyboard

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        auth_url, state = google_auth.get_auth_url(user_id)
        
        context.user_data['oauth_state'] = state
        
        await update.message.reply_text(
            "🔐 **اتصال به Google Drive**\n\n"
            "برای اتصال حساب Google Drive خود، روی دکمه زیر کلیک کنید:",
            parse_mode="Markdown",
            reply_markup=login_keyboard(auth_url)
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا:\n`{str(e)[:200]}`", parse_mode="Markdown")

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if google_auth.is_authenticated(user_id):
        google_auth.logout(user_id)
        await update.message.reply_text("✅ اتصال Google Drive قطع شد.")
    else:
        await update.message.reply_text("⚠️ شما قبلاً متصل نیستید.")
