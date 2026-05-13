# توی handlers/youtube.py، قسمت except رو با این جایگزین کن:

    except Exception as e:
        error_msg = str(e)
        
        if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
            await msg.edit_text(
                "❌ **یوتیوب نیاز به احراز هویت دارد!**\n\n"
                "🔧 **راه حل:**\n"
                "1. فایل cookies.txt را بفرستید\n"
                "2. روی آن ریپلای کنید و `/cookie` بزنید\n"
                "3. دوباره دانلود را امتحان کنید\n\n"
                "📚 راهنما: از افزونه Get cookies.txt LOCALLY استفاده کنید",
                parse_mode="Markdown"
            )
        elif "Requested format is not available" in error_msg or "هیچ فرمتی" in error_msg:
            await msg.edit_text(
                f"{error_msg}\n\n"
                f"💡 **پیشنهاد:**\n"
                f"1. از `/formats {url}` برای دیدن فرمت‌های موجود استفاده کن\n"
                f"2. یا کیفیت پایین‌تر رو امتحان کن\n"
                f"3. یا از `/settings` کیفیت پیش‌فرض رو تغییر بده",
                parse_mode="Markdown"
            )
        elif "Video unavailable" in error_msg:
            await msg.edit_text(
                "❌ **ویدیو در دسترس نیست**\n\n"
                "ممکنه ویدیو حذف شده باشه یا محدودیت جغرافیایی داشته باشه.\n"
                "با cookies می‌تونید محدودیت‌ها رو دور بزنید: `/cookie`",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text(
                f"❌ **خطا در دانلود:**\n`{error_msg[:300]}`\n\n"
                f"🔗 لینک: `{url}`",
                parse_mode="Markdown"
            )
