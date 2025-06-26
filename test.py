import aiohttp
import asyncio
from loader import MERCHANT_ACCOUNT, MERCHANT_PASSWORD

REGULAR_API_URL = "https://api.wayforpay.com/regularApi"


async def suspend_regular(order_reference: str) -> dict:
    payload = {
        "requestType": "SUSPEND",
        "merchantAccount": MERCHANT_ACCOUNT,
        "merchantPassword": MERCHANT_PASSWORD,
        "orderReference": order_reference
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(REGULAR_API_URL, json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as e:
            return {"error": str(e), "orderReference": order_reference}


async def suspend_multiple(order_refs: list[str]):
    tasks = [suspend_regular(ref) for ref in order_refs]
    results = await asyncio.gather(*tasks)
    for res in results:
        print(res)

if __name__ == "__main__":
    order_refs = [
        "invoice_272460617_1733232442",
    ]
    asyncio.run(suspend_multiple(order_refs))
