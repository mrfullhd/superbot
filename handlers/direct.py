from telegram import Update
from telegram.ext import ContextTypes
from core.direct_dl import direct_dl
from core.database import db
from utils.helpers import format_bytes

async def direct_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("📝 `/direct URL`", parse_mode="Markdown")
        return
    
    url = context.args[0]
    msg = await update.message.reply_text("⏳ دانلود مستقیم...")
    
    try:
        file_path = direct_dl.download(url, user_id)
        file_size = file_path.stat().st_size
        
        if file_size < 50 * 1024 * 1024:
            await update.message.reply_document(
                document=open(file_path, "rb"),
                caption=f"✅ {format_bytes(file_size)}"
            )
        
        db.add_history(user_id, "direct", url, str(file_path), file_size)
        db.update_stats(user_id, "direct", file_size)
        
        await msg.edit_text(
            f"✅ دانلود کامل!\n📁 `{file_path.name}`\n📏 `{format_bytes(file_size)}`",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await msg.edit_text(f"❌ `{str(e)[:200]}`", parse_mode="Markdown")
