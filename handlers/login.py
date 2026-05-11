# handlers/login.py

import re
from telegram import Update
from telegram.ext import ContextTypes
from core.google_auth import google_auth

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فرآیند اتصال Google Drive"""
    user_id = update.effective_user.id
    
    try:
        auth_url, state = google_auth.get_auth_url(user_id)
        context.user_data['oauth_state'] = state
        
        await update.message.reply_text(
            "🔐 **اتصال به Google Drive**\n\n"
            "1️⃣ روی لینک زیر کلیک کنید:\n"
            f"[🔗 ورود به Google Drive]({auth_url})\n\n"
            "2️⃣ بعد از تأیید گوگل، یک **خطای 502** می‌بینید. نگران نباشید!\n\n"
            "3️⃣ **آدرس کامل صفحه خطا** را کپی کنید\n\n"
            "4️⃣ آدرس را با دستور زیر بفرستید:\n"
            "`/code آدرس_کامل`\n\n"
            "📋 **مثال:**\n"
            "`/code https://webbot.runflare.run/oauth2callback?state=...&code=...`",
            parse_mode="Markdown",
            disable_web_page_preview=False
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ خطا در ساخت لینک:\n`{str(e)[:200]}`",
            parse_mode="Markdown"
        )

async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    دریافت کد OAuth از URL و تکمیل احراز هویت
    کاربر URL کامل خطای 502 رو می‌فرسته
    """
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "📝 **نحوه استفاده:**\n\n"
            "بعد از کلیک روی لینک `/login` و تأیید گوگل،\n"
            "آدرس صفحه خطا را کپی کنید و با این دستور بفرستید:\n\n"
            "`/code آدرس_کامل_صفحه`\n\n"
            "📋 **مثال:**\n"
            "`/code https://webbot.runflare.run/oauth2callback?state=5358973017&code=4/0AeoWuM...`",
            parse_mode="Markdown"
        )
        return
    
    full_url = context.args[0]
    msg = await update.message.reply_text("🔍 در حال بررسی کد...")
    
    try:
        # استخراج state و code از URL
        state_match = re.search(r'state=(\d+)', full_url)
        code_match = re.search(r'code=([^&\s]+)', full_url)
        
        if not code_match:
            await msg.edit_text(
                "❌ **کد OAuth در آدرس پیدا نشد**\n\n"
                "لطفاً آدرس کامل صفحه خطا را کپی کنید.\n"
                "آدرس باید شامل `code=` باشد.",
                parse_mode="Markdown"
            )
            return
        
        code = code_match.group(1)
        state = state_match.group(1) if state_match else str(user_id)
        
        await msg.edit_text("🔄 در حال تبادل کد با Google...")
        
        # تبادل کد با توکن
        success, result = google_auth.exchange_code(int(state), code, state)
        
        if success:
            await msg.edit_text(
                f"✅ **اتصال موفق!**\n\n"
                f"📧 ایمیل: `{result}`\n\n"
                f"🎉 حالا می‌تونید از Google Drive استفاده کنید!\n"
                f"📥 فایل‌های دانلود شده خودکار آپلود می‌شن.\n\n"
                f"💡 **دستورات:**\n"
                f"`/yt URL` - دانلود ویدیو\n"
                f"`/mp3 URL` - دانلود صدا\n"
                f"`/storage` - مشاهده فضای Drive",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text(
                f"❌ **خطا در اتصال:**\n`{str(result)[:300]}`\n\n"
                f"🔧 **راه حل:**\n"
                f"1. مطمئن شوید آدرس کامل را کپی کرده‌اید\n"
                f"2. دوباره `/login` را بزنید\n"
                f"3. بلافاصله بعد از تأیید، آدرس را کپی کنید",
                parse_mode="Markdown"
            )
        
    except Exception as e:
        await msg.edit_text(
            f"❌ **خطای سیستمی:**\n`{str(e)[:300]}`\n\n"
            f"مطمئن شوید آدرس کامل صفحه خطا را کپی کرده‌اید.",
            parse_mode="Markdown"
        )

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قطع اتصال Google Drive"""
    user_id = update.effective_user.id
    
    if google_auth.is_authenticated(user_id):
        google_auth.logout(user_id)
        await update.message.reply_text(
            "✅ **اتصال Google Drive قطع شد**\n\n"
            "برای اتصال مجدد: `/login`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "⚠️ شما قبلاً متصل نیستید.\n"
            "برای اتصال: `/login`",
            parse_mode="Markdown"
        )
