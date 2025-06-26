import csv
import requests
from collections import defaultdict
from loader import BOT_TOKEN, CHANNEL_ID

TG_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"


def extract_user_id(order_ref: str) -> int | None:
    try:
        prefix, user_id, *_ = order_ref.split("_")
        return int(user_id) if prefix == "invoice" else None
    except Exception:
        return None


def get_telegram_info(user_id: int) -> dict:
    try:
        resp = requests.get(
            TG_API_URL,
            params={"chat_id": CHANNEL_ID, "user_id": user_id},
            timeout=5
        )
        data = resp.json()
        if data.get("ok") and "user" in data.get("result", {}):
            user = data["result"]["user"]
            return {
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "username": user.get("username", "")
            }
    except Exception as e:
        print(f"⚠️ Помилка Telegram API для {user_id}: {e}")
    return {}


if __name__ == "__main__":
    users = defaultdict(list)

    # читаємо регулярки
    with open("regular_statuses.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("status") == "Active":
                uid = extract_user_id(row["orderReference"])
                if uid:
                    users[uid].append(row)

    # знаходимо користувачів з хоча б однією неуспішною оплатою
    expired = []
    for uid, regs in users.items():
        has_failed = any(reg.get("lastPayedStatus") !=
                         "Approved" for reg in regs)
        if has_failed:
            tg_info = get_telegram_info(uid)
            for reg in regs:
                if reg.get("lastPayedStatus") != "Approved" and reg.get("lastPayedStatus"):
                    expired.append({
                        "user_id": uid,
                        "email": reg.get("email", ""),
                        "orderReference": reg.get("orderReference", ""),
                        "lastPayedStatus": reg.get("lastPayedStatus", ""),
                        "lastPayedDate": reg.get("lastPayedDate", ""),
                        **tg_info
                    })

    # зберігаємо лог
    fieldnames = [
        "user_id", "email", "orderReference",
        "lastPayedStatus", "lastPayedDate",
        "first_name", "last_name", "username"
    ]

    with open("expired_regulars.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(expired)

    print(
        f"✅ Готово: записано {len(expired)} прострочених регулярок у expired_regulars.csv")
