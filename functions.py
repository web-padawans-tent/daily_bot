import time

from loader import SECRET_KEY, BOT_TOKEN, CHANNEL_ID, ADMIN_ID, db
from aiogram import Bot
import hmac
import hashlib
import requests

def generate_merchant_signature(merchant_account, merchant_domain, order_reference, order_date, amount, currency, product_name, product_price, product_count):
    signature_string = f"{merchant_account};{merchant_domain};{order_reference};{order_date};{amount};{currency};"
    signature_string += f"{';'.join(product_name)};{';'.join(map(str, product_count))};{';'.join(map(str, product_price))}"
    hash_signature = hmac.new(SECRET_KEY.encode('utf-8'), signature_string.encode('utf-8'), digestmod='md5').hexdigest()
    return hash_signature


def generate_signature(order_reference, status, current_time, secret_key=SECRET_KEY):
    data_string = f"{order_reference};{status};{current_time}"
    signature = hmac.new(secret_key.encode('utf-8'), data_string.encode('utf-8'), digestmod='md5').hexdigest()
    return signature


def extract_user_id_from_reference(order_reference):
    return order_reference.split("_")[1]


def generate_short_link_name(user_id):
    unique_string = f"user_{user_id}_{int(time.time())}"
    short_name = hashlib.md5(unique_string.encode()).hexdigest()[:32]
    return short_name

async def add_user_to_channel(user_id, payment_sys):
    if not db.get_subs(user_id):
        db.add_subs(user_id, payment_sys)
    else:
        db.update_subs(user_id, payment_sys)

    dbuser = db.get_user(user_id)

    bot = Bot(token=BOT_TOKEN)

    await bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)

    # URL для створення посилання
    invite_link_url = f"https://api.telegram.org/bot{BOT_TOKEN}/createChatInviteLink"

    # Параметри посилання
    invite_link_params = {
        "chat_id": CHANNEL_ID,
        "name": generate_short_link_name(user_id),
        "member_limit": 1,  # Обмеження: лише один користувач
        "creates_join_request": False
    }

    # Відправлення запиту на створення посилання
    response = requests.post(invite_link_url, json=invite_link_params)

    if response.status_code == 200:
        invite_link = response.json().get('result', {}).get('invite_link')

        if invite_link:
            # Відправлення посилання користувачу
            message = (
                "Дякуємо за оплату! Ваша місячна підписка на канал LookBook активована.\n\n"
                f"[Перейти до каналу]({invite_link})"
            )

            user_response = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                params={
                    "chat_id": user_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )

            if user_response.status_code == 200:
                # Повідомлення адміністратору
                admin_message = f"Користувач @{dbuser[0]} - {dbuser[1]} успішно доданий до каналу."
                requests.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    params={
                        "chat_id": ADMIN_ID,
                        "text": admin_message
                    }
                )
            else:
                # Помилка надсилання повідомлення користувачу
                print(f"Помилка надсилання повідомлення: {user_response.json()}")
    else:
        # Помилка створення посилання
        error_message = f"Помилка створення запрошення: {response.json()}"
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params={
                "chat_id": ADMIN_ID,
                "text": error_message
            }
        )

def delete_user_from_channel(user_id):
    dbuser = db.get_user(user_id)
    ban_url = f'https://api.telegram.org/bot{BOT_TOKEN}/kickChatMember'
    ban_params = {
        'chat_id': CHANNEL_ID,
        'user_id': user_id
    }
    ban_response = requests.post(ban_url, params=ban_params)

    if ban_response.status_code == 200:
        print("Користувача видалено з каналу.")
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={ADMIN_ID}&text=Користувачa @{dbuser[0]} - {dbuser[1]} видалено каналу!")
    else:
        print("Помилка при видаленні користувача:", ban_response.json())
