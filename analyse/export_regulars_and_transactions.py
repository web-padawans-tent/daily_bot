import csv
import hmac
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from loader import MERCHANT_ACCOUNT, MERCHANT_PASSWORD, SECRET_KEY, BOT_TOKEN, CHANNEL_ID

API_URL = 'https://api.wayforpay.com/api'
REGULAR_API_URL = 'https://api.wayforpay.com/regularApi'
API_VERSION = '2'
MAX_WINDOW = 31 * 24 * 3600  # 31 днів

TG_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"


def extract_user_id(order_reference: str) -> int | None:
    try:
        prefix, user_id, *_ = order_reference.split("_")
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
        if data.get("ok") and "user" in data["result"]:
            user = data["result"]["user"]
            return {
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "username": user.get("username", ""),
                "tg_status": data["result"].get("status", ""),
            }
    except Exception as e:
        print(f"[Telegram] Помилка для {user_id}: {e}")
    return {
        "first_name": "",
        "last_name": "",
        "username": "",
        "tg_status": "unknown"
    }


def check_regular_status(order_reference: str) -> dict:
    payload = {
        "requestType": "STATUS",
        "merchantAccount": MERCHANT_ACCOUNT,
        "merchantPassword": MERCHANT_PASSWORD,
        "orderReference": order_reference
    }
    response = requests.post(REGULAR_API_URL, json=payload)
    response.raise_for_status()
    return response.json()


def get_active_regular(order_ref: str) -> dict | None:
    try:
        data = check_regular_status(order_ref)
        if data.get("status") == "Active":
            user_id = extract_user_id(order_ref)
            telegram_data = get_telegram_info(user_id) if user_id else {}
            return {
                "user_id": user_id or "",
                "orderReference": data.get("orderReference"),
                "status": data.get("status"),
                "amount": data.get("amount"),
                "currency": data.get("currency"),
                "email": data.get("email"),
                "mode": data.get("mode"),
                "dateBegin": datetime.fromtimestamp(data["dateBegin"]).isoformat() if data.get("dateBegin") else "",
                "dateEnd": datetime.fromtimestamp(data["dateEnd"]).isoformat() if data.get("dateEnd") else "",
                "lastPayedDate": datetime.fromtimestamp(data["lastPayedDate"]).isoformat() if data.get("lastPayedDate") else "",
                "lastPayedStatus": data.get("lastPayedStatus", ""),
                "nextPaymentDate": datetime.fromtimestamp(data["nextPaymentDate"]).isoformat() if data.get("nextPaymentDate") else "",
                **telegram_data
            }
    except Exception as e:
        print(f"[WFP] Помилка обробки {order_ref}: {e}")
    return None


def make_signature(merchant_account: str, date_begin: int, date_end: int) -> str:
    raw = f"{merchant_account};{date_begin};{date_end}"
    return hmac.new(SECRET_KEY.encode('utf-8'), raw.encode('utf-8'), digestmod='md5').hexdigest()


def fetch_transactions() -> list:
    dt_from = int(datetime(2023, 1, 1).timestamp())
    dt_to = int(datetime.now().timestamp())
    all_tx = []
    start = dt_from

    while start < dt_to:
        end = min(start + MAX_WINDOW, dt_to)
        payload = {
            "transactionType": "TRANSACTION_LIST",
            "merchantAccount": MERCHANT_ACCOUNT,
            "apiVersion": API_VERSION,
            "dateBegin": start,
            "dateEnd": end,
            "merchantSignature": make_signature(MERCHANT_ACCOUNT, start, end)
        }
        resp = requests.post(API_URL, json=payload)
        resp.raise_for_status()
        body = resp.json()
        chunk = body.get("transactionList", [])
        all_tx.extend(chunk)
        start = end + 1

    return all_tx


if __name__ == "__main__":
    transactions = fetch_transactions()

    order_refs = list({tx.get("orderReference")
                      for tx in transactions if tx.get("orderReference")})

    active_regulars = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(
            get_active_regular, ref): ref for ref in order_refs}
        for future in as_completed(futures):
            result = future.result()
            if result:
                active_regulars.append(result)

    if active_regulars:
        fieldnames = list(active_regulars[0].keys())
        with open("regular_statuses.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(active_regulars)

    print(
        f"✅ Збережено {len(transactions)} транзакцій і {len(active_regulars)} активних регулярок з Telegram-даними.")
