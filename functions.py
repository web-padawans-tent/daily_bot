import time
from logger import app_logger as logger
from loader import SECRET_KEY, BOT_TOKEN, CHANNEL_ID, ADMIN_ID, MERCHANT_ACCOUNT, MERCHANT_PASSWORD, db
from aiogram import Bot
import hmac
import hashlib
import aiohttp


async def get_telegram_info(user_id: int) -> dict:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
    params = {
        "chat_id": CHANNEL_ID,
        "user_id": user_id
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                if data.get("ok") and "user" in data["result"]:
                    user = data["result"]["user"]
                    return {
                        "first_name": user.get("first_name", ""),
                        "last_name": user.get("last_name", ""),
                        "username": user.get("username", ""),
                        "tg_status": data["result"].get("status", ""),
                    }
        except aiohttp.ClientError as e:
            logger.error(f"[Telegram] Помилка aiohttp для {user_id}: {e}")
        except Exception as e:
            logger.error(f"[Telegram] Інша помилка для {user_id}: {e}")

    return {
        "first_name": "",
        "last_name": "",
        "username": "",
        "tg_status": "unknown"
    }


async def suspend_regular(order_reference: str) -> dict:
    if order_reference.startswith("invoice_"):
        parts = order_reference.split("_")
        if len(parts) >= 3:
            order_reference = "_".join(parts[:3])

    payload = {
        "requestType": "SUSPEND",
        "merchantAccount": MERCHANT_ACCOUNT,
        "merchantPassword": MERCHANT_PASSWORD,
        "orderReference": order_reference
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("https://api.wayforpay.com/regularApi", json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as e:
            return {"error": str(e), "orderReference": order_reference}


def generate_merchant_signature(merchant_account, merchant_domain, order_reference, order_date, amount, currency, product_name, product_price, product_count):
    signature_string = f"{merchant_account};{merchant_domain};{order_reference};{order_date};{amount};{currency};"
    signature_string += f"{';'.join(product_name)};{';'.join(map(str, product_count))};{';'.join(map(str, product_price))}"
    hash_signature = hmac.new(SECRET_KEY.encode(
        'utf-8'), signature_string.encode('utf-8'), digestmod='md5').hexdigest()
    return hash_signature


def generate_signature(order_reference, status, current_time, secret_key=SECRET_KEY):
    data_string = f"{order_reference};{status};{current_time}"
    signature = hmac.new(secret_key.encode(
        'utf-8'), data_string.encode('utf-8'), digestmod='md5').hexdigest()
    return signature


def extract_user_id_from_reference(order_reference):
    return order_reference.split("_")[1]


def generate_short_link_name(user_id):
    unique_string = f"user_{user_id}_{int(time.time())}"
    short_name = hashlib.md5(unique_string.encode()).hexdigest()[:32]
    return short_name


async def add_user_to_channel(user_id, payment_sys, order_reference, status=None):
    logger.info(
        f"Запуск додавання користувача {user_id} з оплатою через {payment_sys} та референсом {order_reference}")

    tg_info = await get_telegram_info(user_id)

    if not db.get_subs(user_id):
        db.add_subs(user_id, payment_sys, order_reference,
                    tg_info["username"], status)
        logger.info(
            f"Нова підписка створена для користувача {user_id} з референсом {order_reference}")
    else:
        db.update_subs(user_id, payment_sys, order_reference,
                       tg_info["username"], status)
        logger.info(
            f"Підписка оновлена для користувача {user_id} з референсом {order_reference}")

    dbuser = db.get_user(user_id)

    invite_link_url = f"https://api.telegram.org/bot{BOT_TOKEN}/createChatInviteLink"
    invite_link_params = {
        "chat_id": CHANNEL_ID,
        "name": generate_short_link_name(user_id),
        "member_limit": 1,
        "creates_join_request": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(invite_link_url, json=invite_link_params) as response:
            data = await response.json()

        invite_link = data.get('result', {}).get('invite_link')
        if not invite_link:
            error_message = f"Помилка створення запрошення: {data}"
            logger.error(error_message)
            await session.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                params={"chat_id": ADMIN_ID, "text": error_message}
            )
            return

        logger.info(
            f"Посилання створено для користувача {user_id}: {invite_link}")

        message = (
            "Дякуємо за оплату! Ваша місячна підписка на канал LookBook активована.\n\n"
            f"[Перейти до каналу]({invite_link})"
        )
        user_message_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        user_msg_params = {
            "chat_id": user_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        async with session.get(user_message_url, params=user_msg_params) as user_response:
            if user_response.status == 200:
                logger.info(
                    f"Повідомлення успішно надіслано користувачу {user_id}")
                admin_message = f"Користувач @{dbuser[0]} - {dbuser[1]} успішно доданий до каналу."
                await session.get(
                    user_message_url,
                    params={"chat_id": ADMIN_ID, "text": admin_message}
                )
                logger.info(
                    f"Адміністратор повідомлений про додавання користувача {user_id}")
            else:
                error_text = await user_response.text()
                logger.error(
                    f"Помилка надсилання повідомлення користувачу {user_id}: {error_text}")


async def delete_user_from_channel(user_id, payment_sys, order_reference, status=None):
    logger.info(f"Запуск видалення користувача {user_id} з каналу")

    tg_info = await get_telegram_info(user_id)

    suspend_result = await suspend_regular(order_reference)
    if "reason" in suspend_result:
        logger.info(
            f"Регулярку {order_reference} призупинено: {suspend_result['reason']}")
        db.update_subs(user_id, payment_sys, order_reference,
                       tg_info["username"], status)
        logger.info(
            f"Підписка оновлена для користувача {user_id} з референсом {order_reference}")
    else:
        logger.warning(
            f"Не вдалося призупинити регулярку {order_reference}: {suspend_result}")

    db.payment_attempt(user_id)

    dbuser = db.get_user(user_id)

    bot = Bot(token=BOT_TOKEN)

    ban_url = f'https://api.telegram.org/bot{BOT_TOKEN}/kickChatMember'
    ban_params = {
        'chat_id': CHANNEL_ID,
        'user_id': user_id
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(ban_url, params=ban_params) as ban_response:
            if ban_response.status == 200:
                logger.info(
                    f"Користувача {user_id} успішно видалено з каналу.")

                notify_text = f"Користувачa @{dbuser[0]} - {dbuser[1]} видалено з каналу!"
                await session.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    params={"chat_id": ADMIN_ID, "text": notify_text}
                )
                logger.info(
                    f"Адміністратору надіслано повідомлення про видалення користувача {user_id}")
            else:
                error_data = await ban_response.text()
                logger.error(
                    f"Помилка при видаленні користувача {user_id}: {error_data}")

    try:
        await bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        logger.info(f"Користувач {user_id} розбанений після видалення")
    except Exception as e:
        logger.error(
            f"Помилка при розбані користувача {user_id}: {e}", exc_info=True)
    finally:
        await bot.session.close()
