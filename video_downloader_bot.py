import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import re

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Замените на ваш токен от BotFather
TOKEN = '7983667482:AAHitk8Pm2KuW2e6qt5KT8urtjsN56UChfA'

# Папка для временных файлов
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def is_valid_url(url):
    """Проверяет, является ли URL действительным для поддерживаемых платформ"""
    patterns = [
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/',
        r'(https?://)?(www\.)?(tiktok\.com|vm\.tiktok\.com)/',
        r'(https?://)?(www\.)?(instagram\.com)/',
    ]
    return any(re.search(pattern, url) for pattern in patterns)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_message = (
        "👋 Привет! Я бот для скачивания видео.\n\n"
        "Я могу скачивать видео с:\n"
        "• YouTube\n"
        "• TikTok\n"
        "• Instagram\n\n"
        "Просто отправьте мне ссылку на видео!"
    )
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📖 Как использовать:\n\n"
        "1. Скопируйте ссылку на видео\n"
        "2. Отправьте её мне\n"
        "3. Подождите, пока я скачаю видео\n"
        "4. Получите готовое видео!\n\n"
        "Поддерживаемые платформы:\n"
        "• YouTube (youtube.com, youtu.be)\n"
        "• TikTok (tiktok.com)\n"
        "• Instagram (instagram.com)\n\n"
        "Команды:\n"
        "/start - Начать работу\n"
        "/help - Показать эту справку"
    )
    await update.message.reply_text(help_text)


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Скачивает видео по предоставленной ссылке"""
    url = update.message.text.strip()
    
    if not is_valid_url(url):
        await update.message.reply_text(
            "❌ Пожалуйста, отправьте действительную ссылку на видео с YouTube, TikTok или Instagram."
        )
        return
    
    # Отправляем сообщение о начале загрузки
    status_message = await update.message.reply_text("⏳ Начинаю скачивание видео...")
    
    try:
        # Настройки для yt-dlp
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        # Скачивание видео
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await status_message.edit_text("📥 Скачиваю видео...")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Видео')
        
        # Проверяем размер файла
        file_size = os.path.getsize(filename)
        max_size = 50 * 1024 * 1024  # 50 МБ - лимит Telegram
        
        if file_size > max_size:
            await status_message.edit_text(
                f"❌ Видео слишком большое ({file_size / 1024 / 1024:.1f} МБ). "
                f"Telegram поддерживает файлы до 50 МБ."
            )
            os.remove(filename)
            return
        
        # Отправляем видео
        await status_message.edit_text("📤 Отправляю видео...")
        
        with open(filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"✅ {title}",
                supports_streaming=True
            )
        
        # Удаляем сообщение о статусе
        await status_message.delete()
        
        # Удаляем скачанный файл
        os.remove(filename)
        
    except Exception as e:
        logger.error(f"Ошибка при скачивании: {e}")
        await status_message.edit_text(
            f"❌ Произошла ошибка при скачивании видео.\n"
            f"Попробуйте другую ссылку или повторите попытку позже."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")


async def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запущен!")
    
    # Инициализируем и запускаем приложение
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Держим бота запущенным
    try:
        import signal
        stop_event = asyncio.Event()
        
        # Обработка сигналов для корректной остановки
        def signal_handler(sig, frame):
            stop_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        await stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        # Останавливаем бота
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == '__main__':
    import asyncio
    import sys
    
    # Для Windows устанавливаем правильную политику event loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Создаем и запускаем event loop
    asyncio.run(main())
