import csv
import requests
from collections import defaultdict
from loader import BOT_TOKEN, CHANNEL_ID

INPUT_CSV = "regular_statuses.csv"
OUTPUT_CSV = "illegal_users_in_group.csv"
TG_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"


def is_user_still_in_group(user_id: int) -> bool:
    try:
        response = requests.get(
            TG_API_URL,
            params={"chat_id": CHANNEL_ID, "user_id": user_id},
            timeout=5
        )
        data = response.json()
        if data.get("ok"):
            status = data["result"].get("status")
            return status not in ("left", "kicked")
    except Exception as e:
        print(f"Помилка перевірки Telegram для {user_id}: {e}")
    return False


def extract_user_id(order_reference: str) -> int | None:
    try:
        prefix, user_id, *_ = order_reference.split("_")
        return int(user_id) if prefix == "invoice" else None
    except Exception:
        return None


def get_telegram_info(user_id: int) -> dict:
    try:
        response = requests.get(
            TG_API_URL,
            params={"chat_id": CHANNEL_ID, "user_id": user_id},
            timeout=5
        )
        data = response.json()
        if data.get("ok"):
            user = data["result"]["user"]
            return {
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "username": user.get("username", ""),
                "tg_status": data["result"].get("status", "")
            }
    except Exception as e:
        print(f"Помилка Telegram API для {user_id}: {e}")
    return {
        "first_name": "",
        "last_name": "",
        "username": "",
        "tg_status": "unknown"
    }


if __name__ == "__main__":
    user_regs = defaultdict(list)

    # Читаємо всі регулярки
    with open(INPUT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("status") != "Active":
                continue
            user_id = extract_user_id(row["orderReference"])
            if user_id:
                user_regs[user_id].append(row)

    illegal_users = []

    for user_id, regs in user_regs.items():
        has_valid_payment = any(
            reg.get("lastPayedStatus") == "Approved" or reg.get(
                "lastPayedStatus") == ""
            for reg in regs
        )

        if not has_valid_payment and is_user_still_in_group(user_id):
            tg_info = get_telegram_info(user_id)
            for reg in regs:
                reg["user_id"] = user_id
                reg.update(tg_info)
                illegal_users.append(reg)

    if illegal_users:
        fieldnames = ["user_id", "first_name", "last_name", "username", "tg_status"] + \
            [k for k in illegal_users[0].keys() if k not in (
                "user_id", "first_name", "last_name", "username", "tg_status")]

        with open(OUTPUT_CSV, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(illegal_users)

        print(
            f"⚠️ Знайдено {len(illegal_users)} регулярок у користувачів, які НЕ мали жодної оплати, але ще в групі.")
    else:
        print("✅ Усі користувачі з неоплаченими регулярками вже видалені або мають хоча б одну дійсну оплату.")
