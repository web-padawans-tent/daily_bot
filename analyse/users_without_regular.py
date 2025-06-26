import csv
from telethon.sync import TelegramClient
from telethon.tl.types import User
from loader import CHANNEL_LINK, API_HASH, API_ID, PHONE

# 📄 Файли
INPUT_CSV = "regular_statuses.csv"
OUTPUT_CSV = "users_without_regular.csv"

# 🔎 Функція для витягування user_id з orderReference


def extract_user_id(order_reference: str) -> int | None:
    try:
        prefix, user_id, *_ = order_reference.split("_")
        return int(user_id) if prefix == "invoice" else None
    except Exception:
        return None


def main():
    # Зчитуємо user_id користувачів, у яких є регулярки
    users_with_regulars = set()
    with open(INPUT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = extract_user_id(row["orderReference"])
            if uid:
                users_with_regulars.add(uid)

    # Ініціалізуємо TelegramClient
    client = TelegramClient('session_name', API_ID, API_HASH)
    client.start(PHONE)

    channel = client.get_entity(CHANNEL_LINK)

    # Отримуємо всіх учасників групи
    all_participants = list(client.iter_participants(channel))

    # Відфільтровуємо користувачів без регулярки
    users_without = []
    for user in all_participants:
        if not isinstance(user, User):
            continue
        if user.bot:
            continue
        if user.id not in users_with_regulars:
            users_without.append({
                "user_id": user.id,
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "username": user.username or "",
                "phone": user.phone if hasattr(user, 'phone') else ""
            })

    # Запис результатів у CSV
    if users_without:
        fieldnames = users_without[0].keys()
        with open(OUTPUT_CSV, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users_without)
        print(
            f"📦 Записано {len(users_without)} користувачів без жодної регулярки.")
    else:
        print("✅ Усі учасники групи мають хоча б одну регулярку.")

    client.disconnect()


if __name__ == "__main__":
    main()
