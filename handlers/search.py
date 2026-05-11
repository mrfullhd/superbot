from telegram import Update
from telegram.ext import ContextTypes
from core.youtube_dl import youtube_dl
from keyboards.inline import search_results_keyboard
from utils.helpers import format_duration

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📝 `/search متن جستجو`\nمثال: `/search آهنگ جدید`", parse_mode="Markdown")
        return
    
    query = " ".join(context.args)
    msg = await update.message.reply_text(f"🔍 در حال جستجو: **{query}**", parse_mode="Markdown")
    
    try:
        results = youtube_dl.search(query)
        
        if not results:
            await msg.edit_text("❌ نتیجه‌ای یافت نشد.")
            return
        
        text = f"🔍 **نتایج جستجو برای:** {query}\n\n"
        for i, result in enumerate(results, 1):
            duration = format_duration(result['duration'])
            text += f"{i}. {result['title'][:60]}\n   ⏱ {duration} | `/dl {result['url']}`\n\n"
        
        await msg.edit_text(text, parse_mode="Markdown", reply_markup=search_results_keyboard(results))
        
    except Exception as e:
        await msg.edit_text(f"❌ خطا:\n`{str(e)[:200]}`", parse_mode="Markdown")
