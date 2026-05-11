from telegram import Update
from telegram.ext import ContextTypes
from core.database import db
from keyboards.inline import quality_settings

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings = db.get_user_settings(user_id)
    
    quality = settings.get('quality', 'best')
    text = f"⚙️ **تنظیمات**\n\nکیفیت پیش‌فرض: `{quality}`\n\nبرای تغییر کیفیت انتخاب کنید:"
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=quality_settings())

async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data
    
    if data.startswith("quality_"):
        quality = data.replace("quality_", "")
        settings = db.get_user_settings(user_id)
        settings['quality'] = quality
        db.save_user_settings(user_id, settings)
        
        await query.answer(f"✅ کیفیت روی {quality} تنظیم شد")
        await query.edit_message_text(f"⚙️ کیفیت پیش‌فرض: `{quality}`", parse_mode="Markdown")
    
    elif data == "menu_settings":
        settings = db.get_user_settings(user_id)
        quality = settings.get('quality', 'best')
        await query.edit_message_text(
            f"⚙️ **تنظیمات**\n\nکیفیت: `{quality}`",
            parse_mode="Markdown",
            reply_markup=quality_settings()
        )
