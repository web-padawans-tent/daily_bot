import csv
import json
import requests
from collections import defaultdict
from loader import BOT_TOKEN, CHANNEL_ID

INPUT_CSV = "regular_statuses.csv"
OUTPUT_CSV = "multi_regular_users.csv"


def extract_user_id(order_reference):
    try:
        prefix, user_id, *_ = order_reference.split("_")
        return int(user_id) if prefix == "invoice" else None
    except Exception:
        return None


def get_telegram_info(user_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
    params = {
        "chat_id": CHANNEL_ID,
        "user_id": user_id
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("ok"):
            user = data["result"]["user"]
            return {
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "username": user.get("username", ""),
                "is_bot": user.get("is_bot", False),
                "status": data["result"].get("status", "")
            }
    except Exception as e:
        return {"error": str(e)}
    return {}


def main():
    user_refs = defaultdict(list)
    user_emails = {}

    with open(INPUT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ref = row["orderReference"]
            email = row["email"]
            user_id = extract_user_id(ref)
            if user_id:
                user_refs[user_id].append(ref)
                user_emails[user_id] = email

    filtered = {uid: refs for uid, refs in user_refs.items() if len(refs) > 1}

    rows = []
    for uid, refs in filtered.items():
        tg_info = get_telegram_info(uid)
        row = {
            "user_id": uid,
            "email": user_emails.get(uid, ""),
            "regular_count": len(refs),
            "references": json.dumps(refs, ensure_ascii=False),
            **tg_info
        }
        rows.append(row)

    if rows:
        fieldnames = rows[0].keys()
        with open(OUTPUT_CSV, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    print(
        f"Лог записаний: {len(rows)} користувачів з більш ніж одним регулюванням.")


if __name__ == "__main__":
    main()
