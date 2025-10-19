import telebot
from yt_dlp import YoutubeDL
import os

# -------------------------------
# تنظیمات اولیه
# -------------------------------
BOT_TOKEN = "7487947963:AAGH1T9KAtgVDScyuh56RH32-eHQlYrqwZ4"
DOWNLOAD_DIR = "downloads"
MAX_FILE_SIZE_MB = 49  # حداکثر مجاز تلگرام 50MB است
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = telebot.TeleBot(BOT_TOKEN)


# -------------------------------
# تابع دانلود ویدیو / صوت
# -------------------------------
def download_youtube(url, audio_only=False):
    try:
        opts = {
            "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
            "writethumbnail": True,
        }

        if audio_only:
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        else:
            opts["format"] = "bestvideo+bestaudio/best"
            opts["merge_output_format"] = "mp4"

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if audio_only:
                filename = os.path.splitext(filename)[0] + ".mp3"

            # بررسی حجم فایل
            size_mb = os.path.getsize(filename) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                os.remove(filename)
                return None, info.get("title", "Unknown"), info.get("thumbnail", None), "File too large"

            thumb = info.get("thumbnail", None)
            title = info.get("title", "Unknown")

            return filename, title, thumb, None

    except Exception as e:
        return None, None, None, str(e)


# -------------------------------
# دستورات تلگرام
# -------------------------------
@bot.message_handler(commands=['start'])
def send_welcome(msg):
    bot.reply_to(msg, "👋 سلام! من یه ربات دانلود YouTube هستم.\n"
                      "کافیه بنویسی:\n\n"
                      "🎬 `/mp4 لینک` برای ویدیو\n"
                      "🎧 `/mp3 لینک` برای صوت\n\n"
                      "مثلاً:\n`/mp4 https://youtu.be/dQw4w9WgXcQ`",
                      parse_mode="Markdown")


@bot.message_handler(commands=['mp4'])
def download_video(msg):
    process_download(msg, audio_only=False)


@bot.message_handler(commands=['mp3'])
def download_audio(msg):
    process_download(msg, audio_only=True)


# -------------------------------
# تابع اصلی پردازش دانلود
# -------------------------------
def process_download(msg, audio_only):
    try:
        url = msg.text.split(maxsplit=1)[1]
    except IndexError:
        bot.reply_to(msg, "❗ لطفاً بعد از دستور لینک ویدیو رو بنویس.")
        return

    kind = "🎬 ویدیو" if not audio_only else "🎧 صوت"
    bot.reply_to(msg, f"⏳ در حال دانلود {kind}... لطفاً کمی صبر کن.")

    file_path, title, thumb, error = download_youtube(url, audio_only)

    if error:
        if error == "File too large":
            bot.reply_to(msg, "⚠️ حجم فایل بیشتر از ۵۰ مگابایته و قابل ارسال نیست.")
        else:
            bot.reply_to(msg, f"❌ خطا در دانلود:\n`{error}`", parse_mode="Markdown")
        return

    if not file_path or not os.path.exists(file_path):
        bot.reply_to(msg, "⚠️ خطایی در پردازش فایل رخ داد.")
        return

    caption = f"{kind}: {title}"

    try:
        if not audio_only:
            with open(file_path, "rb") as f:
                bot.send_video(msg.chat.id, f, caption=caption, supports_streaming=True)
        else:
            with open(file_path, "rb") as f:
                bot.send_audio(msg.chat.id, f, caption=caption)

    except Exception as e:
        bot.reply_to(msg, f"❗ خطا در ارسال فایل:\n`{e}`", parse_mode="Markdown")

    # حذف فایل پس از ارسال
    try:
        os.remove(file_path)
    except:
        pass


# -------------------------------
# اجرای ربات
# -------------------------------
print("✅ Bot is running...")
bot.infinity_polling()
