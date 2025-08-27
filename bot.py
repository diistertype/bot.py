import os
from datetime import timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# 1) Получаем токен из переменных окружения
TOKEN = os.environ.get("BOT_TOKEN")

# 2) Тексты (меняй под себя)
AGE_QUESTION = "Вам уже исполнилось 18 лет?"
AGE_REQUIRED = (
    "Доступ ограничен: бот предназначен для пользователей 18+. "
    "Если вам уже есть 18, подтвердите ниже."
)

POST1_TEXT = (
    "🎁 РОЗЫГРЫШ #1\n\n"
    "— iPhone 16 Pro Max\n"
    "— PlayStation 5\n"
    "— AirPods Max\n\n"
    "Условия участия внутри канала 👇"
)

POST2_TEXT = (
    "🎁 РОЗЫГРЫШ #2 (финальный напоминание)\n\n"
    "Последний шанс забрать призы — переходи в канал 👇"
)

# Кнопки для постов (можно поменять URL/подписей)
POST_BUTTONS = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Перейти в канал", url="https://t.me/premium_party01")],
        [InlineKeyboardButton("Связаться", url="https://t.me/premium_party01")],
    ]
)

# 3) Если хочешь отправлять картинку в посте — укажи URL (или оставь None)
POST1_PHOTO_URL = None  # например: "https://your-cdn.com/post1.jpg"
POST2_PHOTO_URL = None  # например: "https://your-cdn.com/post2.jpg"

# 4) Хелперы для отправки постов
async def send_post(chat_id: int, context: ContextTypes.DEFAULT_TYPE, text: str, photo_url: str | None):
    if photo_url:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=photo_url,
            caption=text,
            reply_markup=POST_BUTTONS,
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=POST_BUTTONS,
        )

# 5) /start — задаём вопрос 18+
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Да", callback_data="age_yes"),
                InlineKeyboardButton("Нет", callback_data="age_no"),
            ]
        ]
    )
    await update.effective_chat.send_message(AGE_QUESTION, reply_markup=kb)

# 6) Обработка кликов по кнопкам
async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id

    if data == "age_yes":
        # Подтверждён 18+
        context.user_data["age_verified"] = True
        # Отправляем первый пост
        await send_post(chat_id, context, POST1_TEXT, POST1_PHOTO_URL)
        # Планируем финальный пост через 5 минут
        context.job_queue.run_once(
            callback=send_final_post_job,
            when=timedelta(minutes=5),
            chat_id=chat_id,
            name=f"final_post_{chat_id}",
        )

        # Можно обновить оригинальное сообщение с вопросом
        try:
            await query.edit_message_text("Спасибо! Доступ подтверждён ✅")
        except Exception:
            pass

    elif data == "age_no":
        # Показываем предупреждение и кнопку подтвердить позже
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Да, мне есть 18 лет", callback_data="age_confirm")]]
        )
        try:
            await query.edit_message_text(AGE_REQUIRED, reply_markup=kb)
        except Exception:
            # если нельзя редактировать (например, слишком старое), отправим новое
            await context.bot.send_message(chat_id=chat_id, text=AGE_REQUIRED, reply_markup=kb)

    elif data == "age_confirm":
        # Пользователь передумал и подтвердил
        context.user_data["age_verified"] = True
        await send_post(chat_id, context, POST1_TEXT, POST1_PHOTO_URL)
        context.job_queue.run_once(
            callback=send_final_post_job,
            when=timedelta(minutes=5),
            chat_id=chat_id,
            name=f"final_post_{chat_id}",
        )
        try:
            await query.edit_message_text("Доступ подтверждён ✅")
        except Exception:
            pass

# 7) Джоб: финальный пост через 5 минут
async def send_final_post_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    await send_post(chat_id, context, POST2_TEXT, POST2_PHOTO_URL)

# 8) Дополнительно: /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_message(
        "Команды:\n"
        "/start — начать и подтвердить 18+\n"
        "/help — помощь"
    )

def main():
    if not TOKEN:
        raise RuntimeError("Не найден BOT_TOKEN в переменных окружения.")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(on_button))

    # Запуск бота (long polling)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
