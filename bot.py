import hashlib
import time
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import LabeledPrice, PreCheckoutQuery, Message, ContentType, ChatJoinRequest
from aiogram.filters import Command
from loader import BOT_TOKEN, MERCHANT_DOMAIN, db


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()


@router.chat_join_request()
async def handle_join_request(chat_join_request: ChatJoinRequest):
    chat_id = chat_join_request.chat.id
    user_id = chat_join_request.from_user.id
    text = "Вітаю! 🤍Я адміністратор закритого каналу Daily LookBook від Світлани Косовської. Після оплати ви отримаєте доступ до наших повсякденних образів та натхнення. Чекаємо на вас у нашій спільноті!\n\n<a href='https://lookbookdaily.my.canva.site/pt'>Умови використання</a>\n<a href='https://lookbookdaily.my.canva.site/o'>Договір оферти</a>\n<a href='https://lookbookdaily.my.canva.site/pk'>Політика конфіденційності</a>\n<a href='https://lookbookdaily.my.canva.site/pp'>Політика повернення</a>"
    await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML", reply_markup={"inline_keyboard": [[{"text": "Оплатити", "url": f"{MERCHANT_DOMAIN}/pay/{user_id}"}]]})
    if not(db.user_exists(user_id)):
        db.add_user(user_id, chat_join_request.from_user.username, chat_join_request.from_user.first_name)


async def main():
    await dp.start_polling(bot)


dp.include_router(router)


if __name__ == '__main__':
    import asyncio
    print("Bot started")
    asyncio.run(main())
