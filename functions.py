from loader import SECRET_KEY, BOT_TOKEN, CHANNEL_ID, ADMIN_ID, db
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


def add_user_to_channel(user_id):
    dbuser = db.get_user(user_id)

    invite_link_url = f"https://api.telegram.org/bot{BOT_TOKEN}/createChatInviteLink"

    invite_link_params = {
        "chat_id": CHANNEL_ID,
        "name": "Одноразове посилання",
        "expiration_date": 0,
        "member_limit": 1,
        "creates_join_request": False
    }

    response = requests.post(invite_link_url, json=invite_link_params)

    if response.status_code == 200:
        invite_link = response.json().get('result', {}).get('invite_link')

        if invite_link:
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
                admin_message = f"✅ Пользователь @{dbuser[0]} - {dbuser[1]} успешно добавлен в канал."
                requests.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    params={
                        "chat_id": ADMIN_ID,
                        "text": admin_message
                    }
                )
            else:
                admin_message = (
                    f"❗ Не удалось отправить сообщение пользователю @{dbuser[0]} - {dbuser[1]}. "
                    f"Возможно, пользователь удален или не начал чат с ботом."
                )
                requests.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    params={
                        "chat_id": ADMIN_ID,
                        "text": admin_message
                    }
                )
        else:
            admin_message = "❗ Ошибка при получении ссылки для пользователя."
            requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                params={
                    "chat_id": ADMIN_ID,
                    "text": admin_message
                }
            )
    else:
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
    ban_url = f'https://api.telegram.org/bot{BOT_TOKEN}/banChatMember'
    ban_params = {
        'chat_id': CHANNEL_ID,
        'user_id': user_id
    }
    ban_response = requests.post(ban_url, params=ban_params)

    if ban_response.status_code == 200:
        unban_url = f'https://api.telegram.org/bot{BOT_TOKEN}/unbanChatMember'
        unban_params = {
            'chat_id': CHANNEL_ID,
            'user_id': user_id
        }
        unban_response = requests.post(unban_url, params=unban_params)
        print("Користувача видалено з каналу.")
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={ADMIN_ID}&text=Користувачa @{dbuser[0]} - {dbuser[1]} видалено каналу!")
    else:
        print("Помилка при видаленні користувача:", ban_response.json())

