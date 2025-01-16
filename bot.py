import hashlib
import time
import logging
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.types import LabeledPrice, PreCheckoutQuery, Message, ContentType, ChatJoinRequest, InlineKeyboardButton, \
    InlineKeyboardMarkup
from aiogram.filters import Command
from loader import BOT_TOKEN, MERCHANT_DOMAIN, db

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

@router.chat_join_request()
async def handle_join_request(chat_join_request: ChatJoinRequest):
    user_id = chat_join_request.from_user.id
    username = chat_join_request.from_user.username

    # Текст сообщения
    text = (
        f"Вітаю, {username}! 🤍\n\n"
        "Для того щоб отримати посиляння на оплату. \n\n"
        "Просто натисніть кнопку нижче або надішліть команду /start"
    )

    # Кнопка со ссылкой для начала взаимодействия
    reply_markup = {
        "inline_keyboard": [
            [{"text": "Отримати посилання", "url": f"https://t.me/LookbookDaily_bot?start=start"}]
        ]
    }

    # Отправка сообщения пользователю
    await bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

    if not (db.user_exists(user_id)):
        db.add_user(user_id, chat_join_request.from_user.username, chat_join_request.from_user.first_name)

@router.message(Command("start"))
async def handle_start(message: types.Message):
    user_id = message.from_user.id

    # Текст сообщения
    text = (
        "Вітаю! 🤍Я адміністратор закритого каналу Daily LookBook від Світлани Косовської. "
        "Після оплати ви отримаєте доступ до наших повсякденних образів та натхнення. "
        "Чекаємо на вас у нашій спільноті!\n\n"
        "<a href='https://lookbookdaily.my.canva.site/pt'>Умови використання</a>\n"
        "<a href='https://lookbookdaily.my.canva.site/o'>Договір оферти</a>\n"
        "<a href='https://lookbookdaily.my.canva.site/pk'>Політика конфіденційності</a>\n"
        "<a href='https://lookbookdaily.my.canva.site/pp'>Політика повернення</a>"
    )

    # Кнопка "Оплатить"
    payment_button = InlineKeyboardButton(
        text="Оплатити", url=f"{MERCHANT_DOMAIN}/pay/{user_id}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[payment_button]])

    # Отправка сообщения с кнопкой
    await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML", reply_markup=keyboard)

async def main():
    await dp.start_polling(bot)


dp.include_router(router)

if __name__ == '__main__':
    import asyncio

    print("Bot started")
    asyncio.run(main())
